/* ----------------------------------------------------------- */
/*  2. Appointment iframe page
/* ----------------------------------------------------------- */
    // WHEN CLICK appointment link BUTTON
    jQuery('#mu-auth').on('click', function(event) {
        event.preventDefault();
        $('body').append("<div id='auth-page-popup'><span id='close_auth-page' class='fa fa-close'></span><iframe id='auth-page' name='auth-page' frameborder='0' allowfullscreen></iframe></div>");
        $("#auth-page").attr("src", $(this).attr("href"));
      });
      // WHEN CLICK CLOSE BUTTON
      $(document).on('click','#close_auth-page', function(event) {
        $(this).parent("div").fadeOut(1000);
      });
      // WHEN CLICK OVERLAY BACKGROUND
      $(document).on('click','#auth-page-popup', function(event) {
        $(this).remove();
      });

// // WHEN CLICK APPOINTENT BUTTON
// jQuery('#mu-auth').on('click', function (event) {
//     event.preventDefault();
//     $('#auth-page-popup').fadeIn(1000);
//     $("#auth-page").attr("src", $(this).attr("href"));
// });

// // WHEN CLICK CLOSE BUTTON
// $(document).on('click', '#close-iframe', function (event) {
//     $('#auth-page-popup').fadeOut(1000);
//     // Optionally, you can reset the iframe source to rollback
//     $("#auth-page").attr("src", "");
// });

// // WHEN CLICK OVERLAY BACKGROUND
// $(document).on('click', '#auth-page-popup', function (event) {
//     $('#auth-page-popup').fadeOut(1000);
//     // Optionally, you can reset the iframe source to rollback
//     $("#auth-page").attr("src", "");
// });
