
var current_url = window.location.href;

var sub_url = "generatecalculatedattributedata"

if (current_url.indexOf(sub_url) !== -1) {


    $("[name ='_selected_action']").each(function(){
        var myid = $(this).val();

        setInterval(function() {

            $.ajax({
                // type: "get",
                contentType: 'application/json',
                url: "/pension/plan_calculated_status?plan_attribute_id=" + myid,
                success: function (data) {
                    console.log(data);
                    var status = data.status;
                    var name = data.name;

                    if (status == "in progress") {
                        console.log(myid + " - in progress");
                        $(".status_in_progress").remove();
                        $("#status_calculated").append("<p class='status_in_progress'>" + name + " -  in progress" + "</p>");
                    }
                    // if (status == "done") {
                    //     console.log(myid + " - done");
                    //     $(".status_done").remove();
                    //     //$("#status_calculated").append("<p class='status_done'>"+ name + " -  done" + "</p>");
                    //     $("<p class='status_done'>" + name + " - done" + "</p>").appendTo($("#status_calculated")).fadeOut(3000);
                    //     //$("#status_calculated").append("<p>"+ name + " - done" + "</p>");
                    // }
                }
            });
        }, 7000);
    });
}


