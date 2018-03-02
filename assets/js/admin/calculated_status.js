
var current_url = window.location.href;

var sub_url = "generatecalculatedattributedata";
var arr_id_slected = []

if (current_url.indexOf(sub_url) !== -1) {
    console.log("HERE YOU ARE");
    console.log(task_calculated_id);
    $(".status_in_progress").remove();
    if (task_calculated_id.includes('-')){
        console.log('includes');
        check_task_status();
        var interval = setInterval(check_task_status,7000);
    }

}



function check_task_status(){
    $.ajax({
         type: "get",
         contentType: 'application/json',
         url: "/pension/get_calculated_task_status?task_id=" + task_calculated_id,
         success: function (data) {
             //console.log(data);
             if (data.result === 'PENDING'){
                 console.log(data);
                 $(".status_in_progress").remove();
                 $("#status_calculated").append("<p class='status_in_progress' style='color:red'>" + " Last calculating task -  in progress" + "</p>");

             } else if(data.result === 'SUCCESS'){
                 console.log(data);
                 $(".status_in_progress").remove();
                 $("#status_calculated").append("<p class='status_in_progress' style='color:green'>" + " Last calculating task -  done" + "</p>").delay(5000).fadeOut();
                 clearInterval(interval);
             }
             else {
                 console.log("No task status - no result");
                 $(".status_in_progress").remove();
                 clearInterval(interval);
             }
        },
        error: function(){
             console.log("bad request for get task calculating status");
             $(".status_in_progress").remove();
             clearInterval(interval);
        }
    });
}
    // $("[name ='_selected_action']").each(function(){
    //     var myid = $(this).val();
    //
    //     setInterval(function() {
    //
    //         $.ajax({
    //             // type: "get",
    //             contentType: 'application/json',
    //             url: "/pension/plan_calculated_status?plan_attribute_id=" + myid,
    //             success: function (data) {
    //                 var status = data.status;
    //                 var name = data.name;
    //
    //                 if (status == "in progress") {
    //                     $(".status_in_progress").remove();
    //                     $("#status_calculated").append("<p class='status_in_progress'>" + name + " -  in progress" + "</p>");
    //                 }
    //                 // if (status == "done") {
    //                 //     console.log(myid + " - done");
    //                 //     $(".status_done").remove();
    //                 //     //$("#status_calculated").append("<p class='status_done'>"+ name + " -  done" + "</p>");
    //                 //     $("<p class='status_done'>" + name + " - done" + "</p>").appendTo($("#status_calculated")).fadeOut(3000);
    //                 //     //$("#status_calculated").append("<p>"+ name + " - done" + "</p>");
    //                 // }
    //             }
    //         });
    //     }, 10000);
    // });
// }yes


