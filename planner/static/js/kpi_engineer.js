function ResetFilter() {
    const [workDate, materialType, taskStatus] =
    ['work_date_form', 'material_type_form', 'task_status_form']
    .map(id => document.getElementById(id));

    [workDate, materialType, taskStatus].forEach(el => {el.value = '';});

    document.getElementById('kpi_engineer_form').submit();

};

