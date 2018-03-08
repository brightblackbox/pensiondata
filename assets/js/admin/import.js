// file check
$('#id_import_file').bind('change', function() {

    var error_msg = '';
    has_error = false;
    if(this.files.length === 0){
        error_msg = 'Please choose a data file.'
    }else if(this.files[0].size === 0){
        error_msg = 'It is empty.'
    }else if(this.files[0].size > 5*1024*1024){
        error_msg = 'Max size is 5MB.'
    }

    if (error_msg.length > 0)
        has_error = true;
        $('.error').html(error_msg);

});

// if select format is "xslx" change automatically select from Data Source to Reason
$("#id_input_format").change( function () {
        $("#id_source").val($(this).val());
    }
);

//if select Data source is Reason change automatically select from format to "xlsx"
$("#id_source").change(function () {
    $("#id_input_format").val($(this).val());
});

// form submit
$("#id-import-form").on("submit", function(e){
    e.preventDefault();
    if (has_error){
        return false;
    }

    $('.error').html('');

    var formData = new FormData($(this)[0]);

    $.ajax({
        url: window.location.pathname,
        type: 'POST',
        data: formData,
        async: false,
        cache: false,
        contentType: false,
        enctype: 'multipart/form-data',
        processData: false,

        success: function (resp) {
            console.log(resp);
            if(resp.result === 'success'){
                task_id = resp.task_id;
                job_count = resp.job_count;
                data_source = resp.data_source;
                progress();
            }else if(resp.result === 'fail'){
                $('.error').html(resp.message);

            }else if(resp.result === 'empty'){
                $('.error').html(resp.message);
            }
        }

    });

    return false;
});

// get progress
var progress = function(){
    $("#modal-progress").modal("show");

    var trackIntervalId = setInterval(function() {
        poll();
        if(will_stop === 1){
            clearInterval(trackIntervalId);
            $('.modal-footer').show();
        }
    },interval);
};

var poll = function(){
    $.ajax({
        url: get_progress_url,
        type: 'POST',
        data: {
            task_id: task_id,
            csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val()
        },
        timeout: interval,
        success:
            function(resp) {
                console.log(resp);
                console.log('-----------------------');
                if(resp.result === 'PENDING'){
                    return;
                }

                // if status = PROGRESS

                var percent_now = resp.result.process_percent;
                var imported_count = resp.result.imported_count;

                if(percent_now === null || percent_now === undefined){ // finished
                      will_stop = 1;
                      $('#fill-progress').attr('aria-valuenow', 100).css('width', "100%")
                          .html("100% Done").addClass('progress-bar-success');

                      if (resp.result === 'SUCCESS'){
                          imported_count = 0;
                      }else{
                          imported_count = resp.result;
                      }

                      if (data_source == 'Census'){
                          $('.filled-count').html(imported_count + ": rows processed");
                          $('.failed-count').html((job_count - imported_count) + " failed");
                          $('.total-count').html(job_count + ": Total");
                      }
                      else if (data_source == 'Reason'){
                          $('.filled-count').html(job_count + ": execel sheets are successfully parsed!");
                          $('.total-count').html(job_count + ": Total excel sheets");
                      }


                }else{

                      if(percent_now === 0){
                        $('#fill-progress').attr('aria-valuenow', 10).css('width', "10%")
                          .html("").addClass('progress-bar-success');
                      }else{
                        $('#fill-progress').attr('aria-valuenow', percent_now).css('width', percent_now+"%")
                          .html(percent_now+"%").addClass('progress-bar-success');
                      }
                      $('.filled-count').html(imported_count + ": rows processed");
                      $('.total-count').html(job_count + ": Total");
                }
            },
        error:
            function(resp){
                  console.log(resp);
                  if(resp.statusText === 'timeout'){
                      console.log('timeout');
                      return;
                  }
                  will_stop = 1;
                  $('#fill-progress').attr('aria-valuenow', 100).css('width', "100%")
                      .html("Something was wrong").addClass('progress-bar-danger');
            }
    });// end of ajax
};// end of poll
