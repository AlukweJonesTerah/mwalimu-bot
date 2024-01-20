/* ----------------------------------------------------------- */
/*  2. Appointment iframe page
/* ----------------------------------------------------------- */
    // WHEN CLICK appointment link BUTTON
    jQuery('#mu-booking').on('click', function(event) {
        event.preventDefault();
        $('body').append("<div id='booking-page-popup'><span id='close_booking-page' class='fa fa-close'></span><iframe id='booking-page' name='booking-page' frameborder='0' allowfullscreen></iframe></div>");
        $("#booking-page").attr("src", $(this).attr("href"));
      });
      // WHEN CLICK CLOSE BUTTON
      $(document).on('click','#close_booking-page', function(event) {
        $(this).parent("div").fadeOut(1000);
      });
      // WHEN CLICK OVERLAY BACKGROUND
      $(document).on('click','#booking-page-popup', function(event) {
        $(this).remove();
      });

// // WHEN CLICK APPOINTENT BUTTON
// jQuery('#mu-booking').on('click', function (event) {
//     event.preventDefault();
//     $('#booking-page-popup').fadeIn(1000);
//     $("#booking-page").attr("src", $(this).attr("href"));
// });

// // WHEN CLICK CLOSE BUTTON
// $(document).on('click', '#close-iframe', function (event) {
//     $('#booking-page-popup').fadeOut(1000);
//     // Optionally, you can reset the iframe source to rollback
//     $("#booking-page").attr("src", "");
// });

// // WHEN CLICK OVERLAY BACKGROUND
// $(document).on('click', '#booking-page-popup', function (event) {
//     $('#booking-page-popup').fadeOut(1000);
//     // Optionally, you can reset the iframe source to rollback
//     $("#booking-page").attr("src", "");
// });
