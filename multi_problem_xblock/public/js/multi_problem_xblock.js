function MultiProblemBlock(runtime, element, initArgs) {
  "use strict";
  var $element = $(element);
  var bookmarkButtonHandlers = [];

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


  var {
    current_slide: currentSlide = 0,
    next_page_on_submit: nextPageOnSubmit = false,
  } = initArgs;

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
    // Calculate next slide position
    var nextSlide = currentSlide + n;
    // if you have reached the end of the form...
    if (nextSlide >= slides.length) {
      return false;
    }
    // Hide the current tab:
    slides[currentSlide].style.display = "none";
    currentSlide = nextSlide;
    // Otherwise, display the correct tab:
    showSlide(nextSlide);
  }
  $('.nextBtn', element).click((e) => nextPrev(1));
  $('.prevBtn', element).click((e) => nextPrev(-1));

  /**
   * Reset problems in the given block
   * @param {click even} e
   */
  function resetProblems(e) {
    e.preventDefault();
    // remove all bookmarks under this block as it is possible that a
    // bookmarked block is not selected on reset
    bookmarkButtonHandlers.forEach(function (bookmarkButtonHander) {
      bookmarkButtonHander.removeBookmark();
    });

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
  }

  $('.problem-reset-btn', element).click(resetProblems.bind(this));
  $('.redo-test', element).click(resetProblems.bind(this));

  var $problems = $(element).find('.problems-wrapper');
  var $progressBar = $(element).find('.progress-bar');
  var $resultsBtn = $(element).find('.see-test-results');

  $problems.each(function() {
    $(this).on("progressChanged", function() {
      $.get(runtime.handlerUrl(element, 'get_overall_progress'), function( data ) {
        $progressBar.css('width', data.overall_progress + '%');
        $progressBar.attr('aria-valuenow', data.overall_progress);
        if (data.overall_progress < 100) {
          $resultsBtn.prop('disabled', true);
        } else {
          $resultsBtn.prop('disabled', false);
        }
      });
      // initArgs.nextPageOnSubmit loose value on reset, so confirm value from html template
      if ((nextPageOnSubmit || $('.multi-problem-container', element).data('nextPageOnSubmit'))) {
        nextPrev(1);
      }
    });
  });

  $('.see-test-results', element).click((e) => {
    e.preventDefault();
    $.ajax({
      url: runtime.handlerUrl(element, 'get_test_scores'),
      type: 'GET',
      dataType: 'html',
      success: function( data ) {
        $('.problem-slides-container', element).hide();
        $('.problem-test-score-container', element).html(data);
        var $accordions = $(element).find('.accordion');

        $accordions.each(function() {
          $(this).click(function() {
            var $that = $(this);
            $accordions.each(function() {
              if (!$(this).is($that)) {
                $(this).removeClass("active");
                this.nextElementSibling.style.maxHeight = null;
              }
            });
            $(this).toggleClass("active");
            var panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
              panel.style.maxHeight = null;
            } else {
              panel.style.maxHeight = panel.scrollHeight + "px";
            }
          });
        });

        $('.see-test-results', element).hide();
        $('.problem-reset-btn', element).hide();
        $('.redo-test', element).show();
      }
    });
  })


  window.RequireJS.require(['course_bookmarks/js/views/bookmark_button'], function(BookmarkButton) {
    var $bookmarkButtonElements = $element.find('.multi-problem-bookmark-buttons');
    $bookmarkButtonElements.each(function() {
       bookmarkButtonHandlers.push(new BookmarkButton({
        el: $(this),
        bookmarkId: $(this).data('bookmarkId'),
        usageId: $(this).parent().parent().data('id'),
        bookmarked: $(this).data('isBookmarked'),
        apiUrl: $(this).data('bookmarksApiUrl'),
        bookmarkText: gettext('Bookmark this question'),
      }));
    });
  });
}
