function MultiProblemBlock(runtime, element, initArgs) {
  "use strict";

  var gettext;
  var ngettext;
  if ('gettext' in window) {
    // Use edxapp's global translations
    gettext = window.gettext;
    ngettext = window.ngettext;
  }
  if (typeof gettext == "undefined") {
    // No translations -- used by test environment
    gettext = function(string) { return string; };
    ngettext = function(strA, strB, n) { return n == 1 ? strA : strB; };
  }


  var { current_slide: currentSlide = 0 } = initArgs;
  showSlide(currentSlide)

  function showSlide(n) {
    var slides = $('.slide', element);
    slides[n].style.display = "block";
    //... and fix the Previous/Next buttons:
    if (n == 0) {
      $(".prevBtn", element).prop('disabled', true);
    } else {
      $(".prevBtn", element).prop('disabled', false);
    }
    if (n >= (slides.length - 1)) {
      $(".nextBtn", element).prop('disabled', true);
    } else {
      $(".nextBtn", element).prop('disabled', false);
    }
    //... and run a function that will display the correct step indicator:
    updateStepIndicator(n, slides.length)
  }

  function updateStepIndicator(n, total) {
    $('.slide-position', element).text(
      gettext('{current_position} of {total}').replace('{current_position}', n + 1).replace('{total}', total)
    );
    $.post({
      url: runtime.handlerUrl(element, 'handle_slide_change'),
      data: JSON.stringify({ current_slide: n }),
    });
  }

  function nextPrev(n) {
    // This function will figure out which tab to display
    var slides = $('.slide', element);
    // Hide the current tab:
    slides[currentSlide].style.display = "none";
    // Increase or decrease the current tab by 1:
    currentSlide = currentSlide + n;
    // if you have reached the end of the form...
    if (currentSlide >= slides.length) {
      return false;
    }
    // Otherwise, display the correct tab:
    showSlide(currentSlide);
  }
  $('.nextBtn', element).click((e) => nextPrev(1));
  $('.prevBtn', element).click((e) => nextPrev(-1));

  $('.problem-reset-btn', element).click((e) => {
    e.preventDefault();
    $.post({
      url: runtime.handlerUrl(element, 'reset_selected_children'),
      success(data) {
        edx.HtmlUtils.setHtml(element, edx.HtmlUtils.HTML(data));
        // Rebind the reset button for the block
        XBlock.initializeBlock(element);
        // Render the new set of problems (XBlocks)
        $(".xblock", element).each(function(i, child) {
          XBlock.initializeBlock(child);
        });
      },
    });
  });
}
