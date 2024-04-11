
// 写入csrf
$.getScript("/static/js/csrftoken.js");

$('.vmlalgorithm-delete').click(function(){
      var tr = $(this).closest("tr");
      var vmlalgorithm_id = $(tr).attr("vmlalgorithm-id");
        $('.ui.tiny.modal.delete')
        .modal({
          closable  : true,
          onDeny    : function(){
            return true;
          },
          onApprove : function() {

            $.ajax({
                url: api_vmlalgorithm_delete,
                data: {
                    'vmlalgorithm_id':vmlalgorithm_id,
                    'csrf_token': csrftoken
                },
                type: 'POST',
                dataType: 'json',
                success: function (data) {
                    console.log(data);
                     var code = data.code
                     var msg = data.msg
                     if(code == 0){
                        window.location.reload();
                     }else{
                        alert(msg);
                     }
                },
                error: function(data){
                  alert("error"+data)
                }
            });

          }
        })
        .modal('show');
});


// search
$('#v-search').bind('keypress',function(event){
    var word = $('#v-search').val()
    if(event.keyCode == "13" && word.length > 0)
    {
        window.location = search_url + '?q='+word;
    }
});

$('#search').click(function(){
    var word = $('#v-search').val()
    if(word.length > 0){
        window.location = search_url + '?q='+word;
    }
})