{% block extra_js %}
<script>
let currentCourseId = null;
let modules = [];

// Filter functionality
$('#searchCourse, #filterStatus, #filterSemester').on('keyup change', function() {
    filterCourses();
});

function filterCourses() {
    let search = $('#searchCourse').val().toLowerCase();
    let status = $('#filterStatus').val();
    let semester = $('#filterSemester').val();
    
    $('.course-item').each(function() {
        let code = $(this).data('code').toLowerCase();
        let title = $(this).data('title').toLowerCase();
        let courseStatus = $(this).data('status');
        let courseSemester = $(this).data('semester').toString();
        
        let matchSearch = code.includes(search) || title.includes(search);
        let matchStatus = !status || courseStatus === status;
        let matchSemester = !semester || courseSemester === semester;
        
        if (matchSearch && matchStatus && matchSemester) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

function resetFilters() {
    $('#searchCourse').val('');
    $('#filterStatus').val('');
    $('#filterSemester').val('');
    filterCourses();
}

// Edit Course Functions
function editCourse(courseId) {
    currentCourseId = courseId;
    $.get(`/curriculum/api/course/${courseId}/`, function(data) {
        $('#editCourseCode').text(data.course_code);
        $('#edit_course_code').val(data.course_code);
        $('#edit_course_title').val(data.course_title);
        $('#edit_semester').val(data.semester);
        $('#edit_credits').val(data.credits);
        $('#edit_department').val(data.department);
        $('#edit_lecture_hours').val(data.lecture_hours);
        $('#edit_tutorial_hours').val(data.tutorial_hours);
        $('#edit_practical_hours').val(data.practical_hours);
        $('#edit_total_hours').val(data.total_hours);
        $('#edit_objectives').val(data.course_objectives);
        modules = data.modules || [];
        displayModules();
        $('#num_cos').val(data.num_cos);
        
        // Set course outcomes
        let outcomesText = '';
        if (data.course_outcomes && data.course_outcomes.length) {
            outcomesText = data.course_outcomes.join('\n');
        } else {
            outcomesText = 'CO1: Understand core concepts\nCO2: Apply principles to solve problems\nCO3: Analyze and evaluate solutions\nCO4: Design components\nCO5: Use modern tools';
        }
        $('#course_outcomes').val(outcomesText);
        
        // Store CO-PO mapping data for grid generation
        window.copoMappingData = data.copo_mapping || {};
        
        generateCOPOGrid();
        changeStep(1);
        $('#editCourseModal').modal('show');
    });
}

function changeStep(step) {
    $('.step-content').hide();
    $(`#step${step}Content`).show();
    $('.step').removeClass('active');
    $(`.step[data-step="${step}"]`).addClass('active');
}

function saveBasicInfo() {
    let data = {
        course_code: $('#edit_course_code').val(),
        course_title: $('#edit_course_title').val(),
        semester: $('#edit_semester').val(),
        credits: $('#edit_credits').val(),
        department: $('#edit_department').val(),
        lecture_hours: $('#edit_lecture_hours').val(),
        tutorial_hours: $('#edit_tutorial_hours').val(),
        practical_hours: $('#edit_practical_hours').val(),
        total_hours: $('#edit_total_hours').val()
    };
    
    $.post(`/curriculum/api/course/${currentCourseId}/basic/`, data, function() {
        changeStep(2);
    });
}

function saveObjectives() {
    $.post(`/curriculum/api/course/${currentCourseId}/objectives/`, {
        objectives: $('#edit_objectives').val()
    }, function() {
        changeStep(3);
    });
}

function addModule() {
    let moduleNum = modules.length + 1;
    modules.push({
        module_number: moduleNum,
        module_title: '',
        topics: '',
        teaching_hours: 0
    });
    displayModules();
}

function removeModule(index) {
    modules.splice(index, 1);
    modules.forEach((m, i) => m.module_number = i + 1);
    displayModules();
}

function displayModules() {
    let html = '';
    modules.forEach((module, index) => {
        html += `
            <div class="module-card">
                <h6>Module ${module.module_number}</h6>
                <div class="row">
                    <div class="col-md-12 mb-2">
                        <input type="text" class="form-control" placeholder="Module Title" 
                               value="${escapeHtml(module.module_title)}" onchange="updateModule(${index}, 'title', this.value)">
                    </div>
                    <div class="col-md-12 mb-2">
                        <textarea class="form-control" rows="2" placeholder="Topics covered" 
                                  onchange="updateModule(${index}, 'topics', this.value)">${escapeHtml(module.topics)}</textarea>
                    </div>
                    <div class="col-md-4">
                        <input type="number" class="form-control" placeholder="Teaching Hours" 
                               value="${module.teaching_hours}" onchange="updateModule(${index}, 'hours', this.value)">
                    </div>
                    <div class="col-md-2">
                        <button class="btn btn-danger btn-sm" onclick="removeModule(${index})">Remove</button>
                    </div>
                </div>
            </div>
        `;
    });
    $('#modulesContainer').html(html);
}

function updateModule(index, field, value) {
    if (field === 'title') modules[index].module_title = value;
    if (field === 'topics') modules[index].topics = value;
    if (field === 'hours') modules[index].teaching_hours = parseInt(value);
}

function saveModules() {
    $.post(`/curriculum/api/course/${currentCourseId}/modules/`, {
        modules: JSON.stringify(modules)
    }, function() {
        changeStep(4);
    });
}

// CO-PO Matrix Functions - Shows 1,2,3 values
function generateCOPOGrid() {
    let numCos = parseInt($('#num_cos').val()) || 5;
    let poCount = 12;
    let psoCount = 3;
    
    let html = '<div class="table-responsive">';
    html += '<table class="copo-table"><thead>';
    
    // PO Headers
    html += '<tr><th>CO/PO</th>';
    for (let po = 1; po <= poCount; po++) {
        html += `<th>PO${po}</th>`;
    }
    for (let pso = 1; pso <= psoCount; pso++) {
        html += `<th>PSO${pso}</th>`;
    }
    html += '</tr></thead><tbody>';
    
    for (let co = 1; co <= numCos; co++) {
        html += `<tr class="copo-row" data-co="${co}">`;
        html += `<td class="text-center"><strong>CO${co}</strong></td>`;
        
        // PO values
        for (let po = 1; po <= poCount; po++) {
            let savedValue = 0;
            if (window.copoMappingData && window.copoMappingData[`CO${co}`]) {
                savedValue = window.copoMappingData[`CO${co}`][`PO${po}`] || 0;
            }
            
            let selected3 = (savedValue == 3) ? 'selected' : '';
            let selected2 = (savedValue == 2) ? 'selected' : '';
            let selected1 = (savedValue == 1) ? 'selected' : '';
            let selected0 = (savedValue == 0) ? 'selected' : '';
            
            html += `<td>
                <select class="form-select form-select-sm copo-select" data-co="${co}" data-type="PO" data-po="${po}" style="width: 65px; text-align: center;">
                    <option value="0" ${selected0}>-</option>
                    <option value="1" ${selected1}>1</option>
                    <option value="2" ${selected2}>2</option>
                    <option value="3" ${selected3}>3</option>
                </select>
            </td>`;
        }
        
        // PSO values
        for (let pso = 1; pso <= psoCount; pso++) {
            let savedValue = 0;
            if (window.copoMappingData && window.copoMappingData[`CO${co}`]) {
                savedValue = window.copoMappingData[`CO${co}`][`PSO${pso}`] || 0;
            }
            
            let selected3 = (savedValue == 3) ? 'selected' : '';
            let selected2 = (savedValue == 2) ? 'selected' : '';
            let selected1 = (savedValue == 1) ? 'selected' : '';
            let selected0 = (savedValue == 0) ? 'selected' : '';
            
            html += `<td>
                <select class="form-select form-select-sm copo-select" data-co="${co}" data-type="PSO" data-ps="${pso}" style="width: 65px; text-align: center;">
                    <option value="0" ${selected0}>-</option>
                    <option value="1" ${selected1}>1</option>
                    <option value="2" ${selected2}>2</option>
                    <option value="3" ${selected3}>3</option>
                </select>
            </td>`;
        }
        
        html += '</tr>';
    }
    html += '</tbody></table></div>';
    $('#copoGrid').html(html);
    
    // Add change event listeners
    $('.copo-select').on('change', function() {
        let co = $(this).data('co');
        let type = $(this).data('type');
        let value = $(this).val();
        if (type === 'PO') {
            let po = $(this).data('po');
            console.log(`CO${co} - PO${po} = ${value}`);
        } else {
            let ps = $(this).data('ps');
            console.log(`CO${co} - PSO${ps} = ${value}`);
        }
    });
}

function saveCOPO() {
    let numCos = parseInt($('#num_cos').val()) || 5;
    let courseOutcomes = $('#course_outcomes').val();
    let mapping = {};
    
    // Loop through all PO selects
    $('.copo-select[data-type="PO"]').each(function() {
        let co = $(this).data('co');
        let po = $(this).data('po');
        let value = parseInt($(this).val());
        
        if (!mapping[`CO${co}`]) {
            mapping[`CO${co}`] = {};
        }
        mapping[`CO${co}`][`PO${po}`] = value;
    });
    
    // Loop through all PSO selects
    $('.copo-select[data-type="PSO"]').each(function() {
        let co = $(this).data('co');
        let ps = $(this).data('ps');
        let value = parseInt($(this).val());
        
        if (!mapping[`CO${co}`]) {
            mapping[`CO${co}`] = {};
        }
        mapping[`CO${co}`][`PSO${ps}`] = value;
    });
    
    console.log("Saving CO-PO Mapping:", mapping);
    
    // Send to server
    $.ajax({
        url: `/curriculum/api/course/${currentCourseId}/copo/`,
        type: 'POST',
        data: JSON.stringify({
            num_cos: numCos,
            course_outcomes: courseOutcomes,
            copo_mapping: JSON.stringify(mapping)
        }),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
        },
        success: function(response) {
            if (response.status === 'success') {
                $('#editCourseModal').modal('hide');
                location.reload();
            } else {
                alert('Error saving CO-PO mapping');
            }
        },
        error: function(xhr, errmsg, err) {
            console.log("Error:", xhr.responseText);
            alert('Error saving: ' + errmsg);
        }
    });
}

function submitForApproval(courseId) {
    $('#submitForm').attr('action', `/curriculum/faculty/separate/submit/${courseId}/`);
    $('#submitModal').modal('show');
}

function viewDetails(courseId) {
    $.get(`/curriculum/api/course/${courseId}/`, function(data) {
        let html = `
            <h5>${data.course_code} - ${data.course_title}</h5>
            <hr>
            <p><strong>Semester:</strong> ${data.semester}</p>
            <p><strong>Credits:</strong> ${data.credits}</p>
            <p><strong>Status:</strong> <span class="status-badge status-${data.status}">${data.status_display}</span></p>
            <h6>Course Objectives:</h6>
            <p>${data.course_objectives || 'Not specified'}</p>
            <h6>Modules:</h6>
            ${data.modules && data.modules.length ? data.modules.map(m => `<p><strong>Module ${m.module_number}:</strong> ${m.module_title} (${m.teaching_hours} hours)</p>`).join('') : '<p>No modules added</p>'}
        `;
        $('#detailsContent').html(html);
        $('#viewDetailsModal').modal('show');
    });
}

function trackStatus(courseId) {
    $.get(`/curriculum/api/course/${courseId}/status/`, function(data) {
        let html = `<h5>Approval Timeline</h5><hr>`;
        data.logs.forEach(log => {
            html += `<p><i class="fas fa-clock"></i> ${log.timestamp}<br><strong>${log.action}</strong><br>${log.details}</p><hr>`;
        });
        $('#detailsContent').html(html);
        $('#viewDetailsModal').modal('show');
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Initialize on page load
$(document).ready(function() {
    $('#searchCourse, #filterStatus, #filterSemester').on('keyup change', function() {
        filterCourses();
    });
    
    // When number of COs changes, regenerate grid
    $('#num_cos').on('change', function() {
        generateCOPOGrid();
    });
});
</script>
{% endblock %}