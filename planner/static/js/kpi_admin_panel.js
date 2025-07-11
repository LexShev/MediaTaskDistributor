function ResetFilter() {
    const [workDate, engineers, materialType, taskStatus] =
    ['work_date_form', 'engineers_form', 'material_type_form', 'task_status_form']
    .map(id => document.getElementById(id));

    [workDate, engineers, materialType, taskStatus].forEach(el => {el.value = '';});

    document.getElementById('kpi_form').submit();

};

