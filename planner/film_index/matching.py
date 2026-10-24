"""Сопоставление материалов Oplan3 с каталогом Кинопоиска.

Сигналы: название, год (с допуском ±1 и диапазонами), страна, режиссёр.
Балл - средневзвешенное по ДОСТУПНЫМ с обеих сторон сигналам (если у
материала нет страны/года, они не «штрафуют» совпадение, а исключаются из
знаменателя). Название сравнивается строгой метрикой token_sort_ratio:
token_set_ratio давал ложные 1.0 (короткие названия считались подмножеством).
Режиссёр - полноценный сигнал с большим весом; при неполном совпадении ФИО
(или несовпадении порядка) получает небольшой бонус.
"""

from dataclasses import dataclass, field

from rapidfuzz import fuzz

from film_index import constants, normalization
from film_index.kinopoisk_source import KinopoiskCatalog


@dataclass
class Candidate:
    entry: dict
    score: float
    title_score: float
    year_score: float
    country_score: float
    director_score: float
    director_match: bool
    type_match: bool
    type_known: bool
    year_available: bool
    country_available: bool


@dataclass
class MatchOutcome:
    bucket: str
    best: Candidate = None
    runner_up: Candidate = None
    candidates: list = field(default_factory=list)
    reason: str = ''


def _ratio(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return fuzz.token_sort_ratio(left, right) / 100.0


def _title_similarity(norm_title: str, norm_original: str, entry: dict) -> float:
    """Сходство названия: русское название приоритетно, original — вторично."""
    ru_score = _ratio(norm_title, entry.get('norm_title'))
    original_score = _ratio(norm_original, entry.get('norm_original'))
    return max(
        ru_score,
        original_score * constants.ORIGINAL_TITLE_WEIGHT,
    )


def _country_similarity(query_countries: set, entry_countries: set) -> float:
    if not query_countries or not entry_countries:
        return 0.0
    intersection = query_countries & entry_countries
    return len(intersection) / max(len(query_countries), len(entry_countries))


def _director_component(query: dict, entry: dict):
    """Возвращает (score, match, available) для режиссёров."""
    q_tokens = query['director_tokens']
    c_tokens = entry['director_tokens']
    available = bool(q_tokens) and bool(c_tokens)
    if not available:
        return 0.0, False, False

    if set(query['director_names']) & set(entry['director_names']):
        base = 1.0
    else:
        intersection = q_tokens & c_tokens
        denominator = len(q_tokens) + len(c_tokens)
        base = (2 * len(intersection) / denominator) if denominator else 0.0

    if base >= 1.0:
        score = 1.0
    elif base > 0:
        score = min(1.0, base + constants.DIRECTOR_PARTIAL_BONUS)
    else:
        score = 0.0
    return score, base > 0, True


def _program_kind(program_type_id) -> str:
    if program_type_id in constants.SERIES_TYPES:
        return 'series'
    return 'film'


def build_query(material: dict) -> dict:
    director_names = normalization.director_names(material.get('director'))
    director_tokens = normalization.person_tokens(director_names)
    return {
        'norm_title': normalization.normalize_title(material.get('name')),
        'norm_original': normalization.normalize_title(material.get('orig_name')),
        'years': normalization.parse_years(material.get('production_year')),
        'countries': normalization.normalize_countries(material.get('production_country')),
        'director_names': director_names,
        'director_tokens': director_tokens,
        'kind': _program_kind(material.get('program_type_id')),
    }


def score_candidate(query: dict, entry: dict) -> Candidate:
    title_score = _title_similarity(query['norm_title'], query['norm_original'], entry)

    year_available = bool(query['years']) and entry['year'] is not None
    year_score = 0.0
    if year_available:
        if any(abs(query_year - entry['year']) <= constants.YEAR_TOLERANCE
               for query_year in query['years']):
            year_score = 1.0

    country_available = bool(query['countries']) and bool(entry['countries'])
    country_score = _country_similarity(query['countries'], entry['countries'])

    director_score, director_match, director_available = _director_component(query, entry)

    components = [('title', title_score)]
    if year_available:
        components.append(('year', year_score))
    if country_available:
        components.append(('country', country_score))
    if director_available:
        components.append(('director', director_score))
    numerator = sum(constants.WEIGHTS[key] * value for key, value in components)
    denominator = sum(constants.WEIGHTS[key] for key, _ in components) or 1.0
    total = numerator / denominator

    entry_type = entry.get('type')
    type_known = entry_type in ('film', 'series')
    type_match = (
        type_known
        and query.get('kind') in ('film', 'series')
        and entry_type == query['kind']
    )

    return Candidate(
        entry=entry,
        score=total,
        title_score=title_score,
        year_score=year_score,
        country_score=country_score,
        director_score=director_score,
        director_match=director_match,
        type_match=type_match,
        type_known=type_known,
        year_available=year_available,
        country_available=country_available,
    )


def _sort_key(candidate: Candidate):
    return (candidate.score, candidate.director_match, candidate.type_match)


def match_material(material: dict, catalog: KinopoiskCatalog) -> MatchOutcome:
    query = build_query(material)
    if not query['norm_title'] and not query['norm_original']:
        return MatchOutcome(constants.BUCKET_UNMATCHED, reason='пустое название')

    indices = catalog.candidate_indices(query['norm_title'], query['norm_original'])
    if not indices:
        return MatchOutcome(constants.BUCKET_UNMATCHED, reason='нет кандидатов по токенам')

    best_by_kp = {}
    for index in indices:
        candidate = score_candidate(query, catalog.entries[index])
        kp_id = candidate.entry['kp_id']
        current = best_by_kp.get(kp_id)
        if current is None or _sort_key(candidate) > _sort_key(current):
            best_by_kp[kp_id] = candidate

    scored = sorted(best_by_kp.values(), key=_sort_key, reverse=True)
    same_type = [candidate for candidate in scored if candidate.type_match]
    compatible = [
        candidate
        for candidate in scored
        if candidate.type_match or not candidate.type_known
    ]

    primary = scored
    if same_type and same_type[0].score >= constants.TYPE_FALLBACK_THRESHOLD:
        primary = compatible

    best = primary[0]
    cross_type_primary = best.type_known and not best.type_match
    runner_up = next(
        (
            candidate
            for candidate in primary[1:]
            if candidate.entry['kp_id'] != best.entry['kp_id']
        ),
        None,
    )
    margin = best.score - runner_up.score if runner_up else best.score

    missing_strong = not (best.year_available and best.country_available)
    if cross_type_primary:
        confident = (
            constants.CROSS_TYPE_AUTO
            and best.score >= constants.CROSS_TYPE_AUTO_THRESHOLD
            and best.title_score >= constants.CROSS_TYPE_AUTO_TITLE
            and best.year_available
            and best.year_score >= 1.0
            and margin >= constants.MARGIN
        )
    else:
        confident = (
            best.score >= constants.AUTO_HIGH_THRESHOLD
            and margin >= constants.MARGIN
            and (
                not missing_strong
                or best.title_score >= constants.TITLE_STRICT_FOR_AUTO
            )
        )

    if confident:
        bucket = constants.BUCKET_AUTO_HIGH
    elif best.score >= constants.REVIEW_BAND_THRESHOLD:
        bucket = constants.BUCKET_BAND
    else:
        bucket = constants.BUCKET_AMBIGUOUS

    display = list(primary)
    if not cross_type_primary:
        display.extend(
            candidate
            for candidate in scored
            if candidate.type_known and not candidate.type_match
        )
    display_candidates = []
    seen_ids = set()
    for candidate in display:
        kp_id = candidate.entry['kp_id']
        if kp_id in seen_ids:
            continue
        seen_ids.add(kp_id)
        display_candidates.append(candidate)

    type_label = (
        'ok' if best.type_match
        else 'mismatch' if best.type_known
        else 'unknown'
    )
    reason = (
        f'type={type_label} score={best.score:.3f} margin={margin:.3f} '
        f'title={best.title_score:.3f} year={best.year_score:.1f} '
        f'country={best.country_score:.3f} director={best.director_score:.2f}'
    )
    if cross_type_primary:
        reason += ' fallback=cross_type'
    return MatchOutcome(
        bucket=bucket,
        best=best,
        runner_up=runner_up,
        candidates=display_candidates[:5],
        reason=reason,
    )


def candidates_to_json(candidates: list) -> list:
    payload = []
    for candidate in candidates:
        entry = candidate.entry
        payload.append({
            'kp_id': entry['kp_id'],
            'title': entry['title'],
            'original_title': entry['original_title'],
            'year': entry['year'],
            'countries': sorted(entry['countries']),
            'director': ', '.join(entry['director_names']),
            'type': entry['type'],
            'type_match': candidate.type_match,
            'type_known': candidate.type_known,
            'score': round(candidate.score, 4),
            'title_score': round(candidate.title_score, 4),
            'year_score': candidate.year_score,
            'country_score': round(candidate.country_score, 4),
            'director_score': round(candidate.director_score, 4),
            'director_match': candidate.director_match,
        })
    return payload
