$(function () {
    $('select').selectpicker();
});


$('#search').change( function () {

    var switcher = document.getElementById('switcher')

    if ( switcher.checked == false )    {
        
            document.getElementsByTagName("form")[0].submit();
       
                                        }
});

document.getElementById('switcher').onclick = function() {
    
    if ( this.checked ) {
        
        document.getElementById('Submit').style.display= 'inline-flex'
        document.getElementById('dir').style.display= 'inline-flex'
        document.getElementById('Last_Access').style.display= 'none'
        
        $('#search').data('max-options', false);
        $('#search').data('actions-box', true);
        $('#search').val('').selectpicker('refresh');
        
        $('#search').selectpicker('destroy');
        $('#search').selectpicker();


      
    } else {
        
        document.getElementById('Submit').style.display= 'none'
        document.getElementById('dir').style.display= 'none'
        document.getElementById('Last_Access').style.display= 'inline-flex'

        $('#search').data('max-options', 1);
        $('#search').data('actions-box', false);
        $('#search').val('').selectpicker('refresh');

        $('#search').selectpicker('destroy');
        $('#search').selectpicker();
        
    }

};
