import logging
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger('planner.storage')


class MediaStorage(S3Boto3Storage):
    location = ''
    default_acl = getattr(settings, 'AWS_DEFAULT_ACL', 'private')
    querystring_auth = getattr(settings, 'AWS_QUERYSTRING_AUTH', True)

    def url(self, name, parameters=None, expire=None, http_method=None):
        try:
            saved_domain = self.custom_domain
            self.custom_domain = None
            url = super().url(name, parameters=parameters, expire=expire, http_method=http_method)
            self.custom_domain = saved_domain

            if saved_domain:
                use_ssl = getattr(settings, 'AWS_S3_USE_SSL', False)
                protocol = 'https://' if use_ssl else 'http://'
                url = url.replace(
                    f'{self.endpoint_url}/{self.bucket_name}',
                    f'{protocol}{saved_domain}'
                )

            return url
        except Exception as e:
            logger.warning(f"S3 URL generation failed for '{name}': {e}")
            return ''
