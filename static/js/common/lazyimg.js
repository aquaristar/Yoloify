var LAZY_SETTINGS = {
  'processed-classname': 'lazy-processed',
  'pin-background-class': 'pin-background',
  'more-indicator-id': 'next-part-indicator',
  'next-url-id': 'next-url',
  'old-next-url-id': 'old-next-url'
};

function isMoreIndicatorVisible() {
  var $el = $('#' + LAZY_SETTINGS['more-indicator-id']);
  var el = $el.get(0);
  if (!el) {
    return false;
  }
  var rect = el.getBoundingClientRect();
  if ($('#map').length) {
    var helper = $('#map-pins').get(0);
    var helperRect = helper.getBoundingClientRect();
    return rect.top < (helperRect.top + helperRect.height) + 1000;
    return true;
  } else {
    var wWidth = $(window).width();
    var wHeight = 3 * $(window).height();
    return rect.top < wHeight && rect.bottom > 0 &&
      rect.left < wWidth && rect.right > 0;
  }
}

function appendMoreIndicator() {
  var $pinContainer;
  if ($('#map').length) {
    $pinContainer = $('.pinboard-container');
  } else {
    $pinContainer = $('.pinboard').closest('.container');
  }
  var $loadingDiv = $('#' + LAZY_SETTINGS['more-indicator-id']);

  if ($pinContainer.size() > 0 && $loadingDiv.size() == 0) {
    $loadingDiv = $('<div></div>');
    if (!$('#map').length)
      $loadingDiv.addClass('container');
    $loadingDiv.css('text-align', 'center');
    var $loadingA = $('<a></a>');
    var $loadingText = $('<h4></h4>');
    $loadingText.text('Loading...');
    $loadingText.attr('id', LAZY_SETTINGS['more-indicator-id']);

    $loadingA.append($loadingText);
    $loadingDiv.append($loadingA);
    $pinContainer.after($loadingDiv);
  }
}

function makeScrollHandler(nextUrl, callback) {
  var scrollHandled = false;
  var scrollHandler = function () {
    if (scrollHandled) return;
    if (isMoreIndicatorVisible()) {
      scrollHandled = true;
      var url = nextUrl.data('next-url');
      var xhr = $.ajax({
        type: 'GET',
        url: url
      }).done(function (resp) {
        $('.pinboard').append(resp);
        nextUrl.remove();
        lazyProceed(callback);
      });
      return xhr;
    }
  }
  return scrollHandler;
}

function activateScrollHandling(callback) {
  var $nextUrl = $('#' + LAZY_SETTINGS['next-url-id']);
  var $loadingDiv = $('#' + LAZY_SETTINGS['more-indicator-id']);
  if ($nextUrl.size() > 0) {
    var handler = makeScrollHandler($nextUrl, callback);
    if ($('#map').length) {
      $('#map-pins').unbind('scroll').scroll(handler);
    } else {
      $(window).unbind('scroll').scroll(handler);
    }
  } else {
    $loadingDiv.remove();
  }
}

function lazyPrepare(callback) {
  appendMoreIndicator();
  activateScrollHandling(callback);
}

function lazyStart(callback) {
  appendMoreIndicator();
  var $nextUrl = $('#' + LAZY_SETTINGS['next-url-id']);
  var scrollHandler = makeScrollHandler($nextUrl, callback);
  return scrollHandler();
}

function lazyReset() {
  $(window).unbind('scroll');
  $('#map-pins').unbind('scroll');
  $('.pinboard').empty();
  $('.pinboard-container').css('height', '');
}

function lazyProceed(callback) {
  var $pinboard = $('.pinboard');
  var $pins = $('li.pin', $pinboard).not('.' + LAZY_SETTINGS['processed-classname']);
  var totalCount = $pins.size();
  var processedCount = 0;
  $pins.each(function () {
//      var width = $(window).width() > 479 ? 286 : 110;
    var width = 286;

    var $pin = $(this);
    $pin.addClass(LAZY_SETTINGS['processed-classname']);
    var $img = $('a img', $pin).not('.activity img');
    var origWidth = parseInt($img.attr('width'));
    var origHeight = parseInt($img.attr('height'));
    var destWidth = width - parseInt($pin.css('padding-right'));
    var destHeight = Math.ceil(origHeight * (destWidth / origWidth)) - parseInt($pin.css('padding-top'));

    $pin.hide();
    $pin.css('visibility', 'visible');
    $pin.fadeIn(500);

    $img.css('display', 'inline-block');
    $img.width(destWidth);
    $img.height(destHeight);
    $img.css('visibility', 'hidden');
    $img.load(function () {
      $img.hide();
      $img.css('visibility', 'visible');
      $img.fadeIn(500);
    }).attr('src', $img.data('src'));

    ++processedCount;
    if (processedCount == totalCount && callback) {
      $('li.pin').wookmark({
        autoResize: true,
        container: $pinboard.parent(),
        offset: 0,
        outterOffset: 0,
        itemWidth: width,
        flexibleWidth: true
      });

      lazyPrepare(callback);    // enable the next part loading
      callback();
    }
  });
  if (totalCount == 0) {
    lazyPrepare(callback);    // enable the next part loading
    callback();
  }

}

function lazyImageLoad(element, callback) {
  var $items = $(element);
  var totalCount = $items.size();
  var processedCount = 0;

  if (totalCount == 0) {
    callback();
  }
  $items.each(function () {
    var $item = $(this);
    var $img = $('a img', $item);
    var width = parseInt($img.attr('width'));
    var height = parseInt($img.attr('height'));

    $img.css('display', 'inline-block');
    $img.width(width);
    $img.height(height);
    $img.css('visibility', 'hidden');

    $img.load(function () {
      $item.css('visibility', 'visible');
      $img.hide();
      $img.css('visibility', 'visible');
      $img.fadeIn(500);
    }).attr('src', $img.data('src'));

    ++processedCount;
    if (processedCount == totalCount && callback) {
      callback();
    }
  });
}

