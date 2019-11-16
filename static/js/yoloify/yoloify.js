var DEBUG = true;

$(function () {
  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  $.ajaxSetup({
    timeout: 10000,
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type)) {
        xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
      }
    }
  });

  { // Append trailing slash to Backbone.Model.url()
    var _url = Backbone.Model.prototype.url;
    Backbone.Model.prototype.url = function () {
      var original_url = _url.call(this);
      var parsed_url = original_url + (original_url.charAt(original_url.length - 1) == '/' ? '' : '/');

      return parsed_url;
    }
  }

  // For every modal bind every pointing link (a/button)
  $('.modal').each(function () {
    var modal = $(this);
    var id = modal.attr('id');
    if (id) {
      $(document).on('click', '[data-modal^=#' + id + ']', function () {
        // if it's being clicked from another modal - hide it
        var fromModal = $(this).closest('.modal');
        if (fromModal && !fromModal.hasClass('static')) fromModal.modal('hide');

        modal.modal();
        return false; // prevent default
      });
    }
  });

  $(document).on("click", ".pin .like", function (e) {
    e.preventDefault();
    if ($('body').hasClass('unauth')) {
      $("[data-modal=#loginModal]").click();
    } else {
      var goalId = $(this).data("goalId");
      var pinId = $(this).data("pinId");
      var pin = $(this).closest(".pin");
      var like = $(this);

      pin.addClass('like-loading');

      $.post("/api/like/", {
        goal_id: goalId,
        pin_id: pinId
      }, function (response) {
        pin.find(".l .count").html(response.count);
        if (response.liked) {
          like.addClass("liked");
          like.attr('data-original-title', 'Unlike');
        } else {
          like.removeClass("liked");
          like.attr('data-original-title', 'Like');
        }
        pin.removeClass('like-loading');
      });
    }
  });

  $(document).on("click", ".pin .repost", function (e) {
    e.preventDefault();
    if ($('body').hasClass('unauth')) {
      $("[data-modal=#loginModal]").click();
    } else {
      var goalId = $(this).data("goalId");
      var pinId = $(this).data("pinId");
      var pin = $(this).closest(".pin");
      var repost = $(this);
      pin.addClass('repost-loading');

      $.post("/api/bookmark/", {
        goal_id: goalId,
        pin_id: pinId
      }, function (response) {
        pin.find(".p .count").html(response.count);
        if (response.bookmarked) {
          repost.addClass("reposted");
          repost.attr('data-original-title', 'Remove from Bookmarks');
          ga('send','content_action','bookmark_pinpart',window.location.href);  //Google Analytics Event Tracking
        } else {
          repost.removeClass("reposted");
          repost.attr('data-original-title', 'Add to Bookmarks');
          ga('send','content_action','unbookmark_pinpart',window.location.href); //Google Analytics Event Tracking
        }
        pin.removeClass('repost-loading');
      });
    }
  });

  $(document).on('touchstart', '.pin a.zoom', function () {
    $(this).mouseenter();
  }).on('touchend', '.pin a.zoom', function () {
    $(this).mouseleave();
  });

  {
    var $modal = $('#contactFormModal');
    var contact_form = new AjaxForm({
      el: $('form', $modal),
      onSuccess: function (data) {
        $modal.modal('hide');
      },
      onErrors: function () {
        $('.modal-content', $modal).effect('shake');
      }
    });
  }

});


var Goal = Backbone.Model.extend({
  urlRoot: '/api/goals'
});


var Pin = Backbone.Model.extend({
  urlRoot: '/api/pins'
});

var PinModal = Backbone.View.extend({
  el: $("#pinModal"),

  events: {
    'click a.repost': 'repost',
    'click a.delete': 'destroy',
    'click a.like': 'like',
    'click a.complete': 'complete',
    'focus textarea.content': 'show_comment_button',
    'click .add-comment': 'submit_comment',
    'click a.flag-comment': 'flag_comment',
    'click a.toggle-map': 'show_map',
    'click .pin-address': 'show_map'
  },

  initialize: function () {
    this.model.on('change', this.render, this);
    this.baseUrl = window.location.href;
    this.$el.toggleClass('static', this.options.static == true);
    this.geoCoder = new google.maps.Geocoder();
  },

  render: function () {
    if (this.model.hasChanged()) {
      var description = this.model.get('description');
      this.$('.description').html(description).toggle(!!description);
      this.$('.title').html(this.model.get('title'));
      this.$('[data-dismiss=modal]').toggle(!this.options.static);

      var avatar_url = this.model.get('author_image') || '/static/img/userpic.png';
      this.$('.reposted .avatar-link').attr('href', '/profile/' + this.model.get('author_id') + '/');
      this.$('.reposted .avatar').attr('src', avatar_url).attr('alt', this.model.get('author')).attr('title', this.model.get('author'));
      this.$('.reposted .name').html('<a href="/profile/' + this.model.get('author_id') + '/">' + this.model.get('author') + '</a>');
      this.$('.reposted .date').html(moment(this.model.get('goal_created')).fromNow());
      if (this.model.hasChanged('image')) {
          var image = this.$('img.image');
          var hiddenimage = $('<img />').load(function () {
            image.attr('src', $(this).attr('src'));
          }).attr('src', this.model.get('image_url'));
        }
      var view = this;
      this.$('.fb-share').off('click').on('click', function (event) {
        FB.ui({
          method: 'share',
          href: window.location.href
        }, function (response) {
        });
        return false;
      });

      this.$('.fb-message').off('click').on('click', function (event) {
        ga('send','share','plan_fb',window.location.href);  //Google Analytics Event Tracking
        FB.ui({
          method: 'send',
          link: window.location.href
        }, function (response) {
        });
        return false;
      });

      this.$el.toggleClass('reposted', this.model.get('is_bookmarked_by_me'));
      this.$el.toggleClass('owner', this.model.get('is_owner'));
      this.$el.toggleClass('goal-owner', this.model.get('is_goal_owner'));
      if (this.model.get('is_completed_by_me') && !$('body').hasClass('unauth')) {
        this.$el.addClass('completed');
      } else {
        this.$el.removeClass('completed');
      }

      this.$el.find(".count-bookmark").html(this.model.get("pin_count"));
      this.$el.find(".count-been-here").html(this.model.get("complete_count"));
      this.$el.find(".count-review").html(this.model.get("comment_count"));
      this.$el.find("a.like").toggleClass("liked", this.model.get("is_liked_by_me"));
      this.$el.find("a.repost").toggleClass("reposted", this.model.get('is_bookmarked_by_me'));
      this.$el.find("a.complete").toggleClass("completed", this.model.get("is_completed_by_me"));
      if(this.model.get('is_bookmarked_by_me')){
        this.$el.find(".bookmark-text").html("Bookmarked");
      }

      //Tooltip
      var bookmarkTitle = this.model.get('is_bookmarked_by_me') ? "Remove from Bookmarks" : "Add to Bookmarks";
      this.$el.find("a.repost").attr('data-original-title', bookmarkTitle);
      var likeTitle = this.model.get('is_liked_by_me') ? "Unlike" : "Like";
      this.$el.find("a.like").attr('data-original-title', likeTitle);
      var completeTitle = this.model.get('is_completed_by_me') ? "Haven't Been Here" : "Been Here";
      this.$el.find("a.complete").attr('data-original-title', completeTitle);

      if (this.model.get("site_url") != null && this.model.get("site_url") != "") {
        if (this.model.get("site_url").substring(0, 7) != "http://" && this.model.get("site_url").substring(0, 7) != "https://") {
          this.$el.find(".website").attr("href", "http://" + this.model.get("site_url")).show();
        } else {
          this.$el.find(".website").attr("href", this.model.get("site_url")).show();
        }
      } else {
        this.$el.find(".website").hide();
      }
      
      
      //allows user to send pin url via text message
      if( /Android/i.test(navigator.userAgent) ) {
        this.$('.mobile-txt').off('click').on('click', function (event) {
  
          var url = 'sms: ?body= ' +  window.location.href + '';
          window.open(url,'_self');
        });
      } else if( /iPhone|iPad|iPod|CriOS/i.test(navigator.userAgent) ) {
          this.$('.mobile-txt').off('click').on('click', function (event) {
            ga('send','share','plan_text',window.location.href);  //Google Analytics Event Tracking
            var url = 'sms: &body= ' +  window.location.href + '';
            window.open(url,'_self');
          });
   
      } else {
        this.$el.find(".mobile-txt").hide();
      }


      if (this.model.get("deal_button_link") && this.model.get("deal_active")) {
        this.$el.find(".actionBtn").html('<span class="glyphicon glyphicon-tag"></span> View Available Deal');
        this.$el.find(".actionBtn").attr("href", this.model.get("deal_button_link")).show();

      } else {

        if (this.model.get("action_button_text")) {
          this.$el.find(".actionBtn").html('<span class="glyphicon glyphicon-calendar"></span> ' + this.model.get("action_button_text"));
          this.$el.find(".actionBtn").attr("href", this.model.get("action_button_link")).show();
        } else {
          this.$el.find(".actionBtn").hide();
        }
      }

      if (this.model.get('type') == 'location') {
        this.$el.find(".pin-location-module").show();
        this.$el.find(".pin-category-name").html(this.model.get("category_name"));

        this.$el.find(".pin-l-category-info").hide();
        this.$el.find(".pin-category-detail div").hide();
        if (this.model.get("category_is_hike") == true && this.model.get("hike_detail") != "") {
          try {
            var hikeDetail = JSON.parse(this.model.get("hike_detail"));

            if (hikeDetail.trail && hikeDetail.trail.amount) {
              this.$el.find(".pin-category-detail-trail").show().find("span").html(hikeDetail.trail.amount + " " + hikeDetail.trail.unit);
            }
            if (hikeDetail.elevation && hikeDetail.elevation.amount) {
              this.$el.find(".pin-category-detail-elevation").show().find("span").html(hikeDetail.elevation.amount + " " + hikeDetail.elevation.unit);
            }
            if (hikeDetail.highest && hikeDetail.highest.amount) {
              this.$el.find(".pin-category-detail-highest").show().find("span").html(hikeDetail.highest.amount + " " + hikeDetail.highest.unit);
            }
            if (hikeDetail.trail && hikeDetail.trail.amount && hikeDetail.elevation && hikeDetail.elevation.amount && (hikeDetail.trail.unit == "Miles" && hikeDetail.elevation.unit == "Feet")) {

              var hike_length = parseFloat(hikeDetail.trail.amount);
              var hike_gain = parseFloat(hikeDetail.elevation.amount);
              var hike_score = ((.002 * hike_gain) + hike_length);
              var hike_difficulty;
              //Easy hike
              if (hike_score > 0 && hike_score < 6) {
                hike_difficulty = "Easy";
              }
              //Moderate hike
              if (hike_score >= 6 && hike_score < 11) {
                hike_difficulty = "Moderate";
              }
              //Difficult hike
              if (hike_score >= 11) {
                hike_difficulty = "Hard";
              }


              this.$el.find(".pin-category-detail-difficulty").show().find("span").html(hike_difficulty);
            }
            this.$el.find(".pin-l-category-info").show();
          } catch (e) {
          }
        }
        this.$el.find('.pin-category-text').html(this.model.get('category_name'));
        
        this.$el.find('.pin-phone-number').toggle(!!this.model.get('phone_number')).find('.desktop-phone').html(this.model.get('phone_number'));
       
        if (this.model.get("phone_number") != null && this.model.get("phone_number") != "") {
          this.$el.find(".mobile-phone-link").attr("href", 'tel:' + this.model.get('phone_number')).show();
        } else {
          this.$el.find(".mobile-phone-link").hide();
        }

        this.$el.find("#pin-map-canvas").hide();
        this.$el.find("a.toggle-map").removeClass("open");
        this.$('.copyright').toggle(this.model.get('image_author') != '');
        this.$('.copyright a').attr('href', this.model.get('image_source')).html(this.model.get('image_author'));
        if (!this.model.get('image_source')) this.$('.copyright a').removeAttr('href');
      } else {
        this.$el.find(".pin-location-module").hide();
      }
      if (this.model.get('l_address')) {
        var url;
          if (/Android/i.test(navigator.userAgent)) {
            url = 'geo:0,0?q=';
          } else if (/iPhone|iPad|iPod|CriOS/i.test(navigator.userAgent)) {
              url = 'http://maps.apple.com/?daddr=';
          } else {
              url = 'https://www.google.com/maps?daddr=';
          }
          this.$('a.directions').attr('href', url + encodeURIComponent(this.model.get('l_address')));
      }
      this.load_pin_comments(this.model);
      // Render features
      var features = this.model.get('features');
      this.$('.pin-features').toggle(!!features);
      if (features) {
        features = features.split(',');
        this.$('.pin-features ul').empty();
        for (var index in features) {
          var encoded = encodeURIComponent(features[index]);
          if(features[index] != ""){
            var $li = $('<li></li>').html('<a id="tag-search" href="/search/?query=' + encoded + '">' + features[index] + '</a>');
          }
          this.$('.pin-features ul').append($li);
        }
      }
      // Render tags
      var tags = this.model.get('tags');
      this.$('.pin-tags').toggle(!!tags);
      if (tags) {
        tags = tags.split(',');
        this.$('.pin-tags ul').empty();
        for (var index in tags) {
          var encoded = encodeURIComponent(tags[index]);
          if(tags[index] != ""){
            var $li = $('<li></li>').html('<a id="tag-search" href="/search/?query=' + encoded + '">' + tags[index] + '</a>');
          }
          this.$('.pin-tags ul').append($li);
        }
      }
      view.renderOperatingHours();
      view.parseAddress();
    }
  },
  renderOperatingHours: function () {
    var operatingHours = this.model.get('operating_hours');
    var $operationHourElem = this.$el.find('.pin-operating-hours');
    if (_.isEmpty(operatingHours)) {
      $operationHourElem.hide();
    } else {
      $operationHourElem.show();
      var days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      var html = '';
      _.each(days, function (day) {
        var dayHtml = '';
        _.each(operatingHours[day], function (hour) {
          if (dayHtml) {
            dayHtml += '<br> <span>' + hour.open + ' - ' + hour.close + '</span>';
          } else {
            dayHtml += '<span>' + hour.open + ' - ' + hour.close + '</span>';
          }
        });
        if (dayHtml) {
          html += '<div><div class="day-hours">' + day + ': </div><div class="time-hours">' + dayHtml + '</div></div>'
        } else {
          html += '<div><div class="day-hours">' + day + ': </div><div class="time-hours"> Closed </div></div>'
        }
      });
      $operationHourElem.find('div').html(html);
    }
  },
  showSidebarMap: function () {
    if (this.model.get("type") != "location") {
      return false;
    }
    this.load_map('#sidebar-map-canvas');
  },
  show_map: function () {
    if (this.model.get("type") != "location") {
      return false;
    }
    if (this.$el.find("#pin-map-canvas").is(":visible")) {
      this.$el.find("#pin-map-canvas").hide();
      this.$el.find("a.toggle-map").removeClass("open");
      return false;
    }
    this.$el.find("a.toggle-map").addClass("open");
    this.$el.find("#pin-map-canvas").show();
    this.load_map('#pin-map-canvas');
  },

  load_map: function (elementId) {
    var mapDiv = this.$(elementId).get(0);
    var jsonBounds = JSON.parse(this.model.get('l_bounds'));
    try {
      var jsonPlace = JSON.parse(this.model.get('l_place'));
    } catch (e) {

    }
    var place = new google.maps.LatLng(jsonPlace.lat, jsonPlace.lng);
    var mapOptions = {
      mapTypeId: google.maps.MapTypeId.ROADMAP,
      zoom: 9,
      center: place
    };
    map = new google.maps.Map(mapDiv, mapOptions);
    var marker = new google.maps.Marker({
      position: place,
      map: map,
      draggable: false,
      title: this.model.get('l_address')
    });
    return false;
  },

  syncComplete: function (jqXHR, textStatus) {
    var error = this.$('.modal-body .error');
    this.$el.addClass('has-error');
    if (textStatus == 'timeout') {
      error.html('Server does not respond. Check your connection and try again.');
    } else if (textStatus == 'error') {
      if (DEBUG) error.html('<pre>' + jqXHR.responseText + '</pre>');
      else error.html('Something went wrong. Please try again later.')
    } else {
      this.$el.removeClass('has-error');
    }
  },

  open: function () {
    var $loader = $('#pinModalLoader');
    $loader.show();
    if (this.xhr) this.xhr.abort();
    this.xhr = this.model.fetch({
      success: _.bind(function () {
        var $img = this.$('img.image');
        var imageFetched = false;
        var modalOptions = {
          show: true,
          backdrop: this.options.static ? false : true
        };
        this.syncComplete();
        if (!this.options.dontPushState) {

          var previousURL = window.location.href;
          window.history.pushState('pin' + this.model.id, 'Pin #' + this.model.id, '/pin/' + this.model.id + '/' + this.model.get('slug_title') + '/');
          
          window.onpopstate = function(event) {
            $('#pinModal').modal('hide');
          };
          
          this.$el.one('hide.bs.modal', function () {
            if(previousURL != window.location.href){
              	window.history.back();
            }
          });
          
          $.get("https://graph.facebook.com/?id=" + window.location.href + "&scrape=true"); //updates facebook opengraph cache 
          ga('send','content_action','view_pinmodal',window.location.href);  //Google Analytics Event Tracking

        }
       if (this.model.hasChanged('image')) {
          $img.one('load', _.bind(function () {
            if (!imageFetched) {
              this.$el.modal(modalOptions);
              var baseUrl = this.baseUrl;
              this.trigger('open');
              $loader.hide();
              imageFetched = true;
            }
          }, this)).attr('src', this.model.get('thumb_url'));
        } else {
          this.$el.modal(modalOptions);
          this.trigger('open');
          $loader.hide();
        }
      }, this)
    });
  },

  close: function () {
    this.$el.modal('hide');
  },

  like: function (event) {
    if ($('body').hasClass('unauth')) {
      $("[data-modal=#loginModal]").click();
    } else {
      var pin = $("a[data-id='" + this.model.get('id') + "']").closest(".pin");
      var likelnk = this.$el.find("a.like").add(pin.find("a.like"));
      var counts = this.$el.find(".l .count").add(pin.find(".l .count"));

      var $el = this.$el;
      $el.addClass('like-loading');
      $.post("/api/like/", {
        goal_id: this.model.get("goal"),
        pin_id: this.model.get("id")
      }, function (response) {
        counts.html(response.count);
        if (response.liked) {
          likelnk.addClass("liked");
          likelnk.attr('data-original-title', 'Unlike');
        } else {
          likelnk.removeClass("liked");
          likelnk.attr('data-original-title', 'Like');
        }
        $el.removeClass('like-loading');
      });
    }
  },

  complete: function (event) {
    if ($('body').hasClass('unauth')) {
      $("[data-modal=#loginModal]").click();
    } else {
      var pin = $("a[data-id='" + this.model.get('id') + "']").closest(".pin");
      var completelnk = this.$el.find("a.complete").add(pin.find("a.complete"));
      var counts = this.$el.find(".c .count").add(pin.find(".c .count"));

      var $el = this.$el;
      $el.addClass('complete-loading');
      $.post("/api/complete/", {
        goal_id: this.model.get("goal"),
        pin_id: this.model.get("id")
      }, function (response) {
        counts.html(response.count);
        if (response.completed) {
           $("#review-box").focus();
          completelnk.addClass("completed");
          completelnk.attr('data-original-title', "Haven't Been Here");
          ga('send','content_action','beenhere_modal',window.location.href);  //Google Analytics Event Tracking
         
        } else {
          completelnk.removeClass("completed");
          completelnk.attr('data-original-title', ' Been Here');
          ga('send','content_action','unbeenhere_modal',window.location.href);  //Google Analytics Event Tracking
        }
        $el.removeClass('complete-loading');
      });
    }
  },

  repost: function () {
    if ($('body').hasClass('unauth')) {
      $("[data-modal=#loginModal]").click();
    } else {
      var pin = $("a[data-id='" + this.model.get('id') + "']").closest(".pin");
      var bookmarklnk = this.$el.find("a.repost").add(pin.find("a.repost"));
      var bookmarktxt= this.$el.find(".bookmark-text").add(pin.find(".bookmark-text"));
      
      var counts = this.$el.find(".p .count").add(pin.find(".c .count"));
      var $el = this.$el;
      $el.addClass('repost-loading');
      $.post("/api/bookmark/", {
        goal_id: this.model.get("goal"),
        pin_id: this.model.get("id")
      }, function (response) {
        counts.html(response.count);
        if (response.bookmarked) {
          bookmarklnk.addClass("reposted");
          bookmarklnk.attr('data-original-title', 'Remove from Bookmarks');
          bookmarktxt.html("Bookmarked");
          ga('send','content_action','bookmark_modal',window.location.href);  //Google Analytics Event Tracking
        } else {
          bookmarklnk.removeClass("reposted");
          bookmarklnk.attr('data-original-title', 'Add to Bookmarks');
          bookmarktxt.html("Bookmark it");
          ga('send','content_action','unbookmark_modal',window.location.href); //Google Analytics Event Tracking
        }
        $el.removeClass('repost-loading');
      });
    }
  },

  destroy: function (event) {
    event.preventDefault();
    var that = this;

    bootbox.confirm("Are you sure you want to remove the pin from your profile?", function (result) {
      if (result) {
        that.model.destroy({
          'complete': _.bind(that.destroyComplete, that)
        });
      }
    });
    return false;
  },

  destroyComplete: function (jqXHR, textStatus) {
    if (textStatus == 'timeout') {
    } else if (textStatus == 'error') {
    } else {
      this.trigger('destroy');
    }
  },

  load_pin_comments: function (model) {
    var pin = model.toJSON(),
      $comment_module = this.$el.find('.pin-comment-module');

    if (!pin.goal) return false;

    $.ajax({
      url: '/api/comments/?content_type=pinboard.goal&object_pk=' + pin.goal + '&pin_id=' + pin.id,
      method: 'GET'
    }).done(function (data, textStatus, jqXHR) {
      $comment_module.html(data);
      $comment_module.show();
    }).fail(function () {
      $comment_module.html('');
      $comment_module.hide();
    });
  },
  show_comment_button: function (e) {
    e.preventDefault();
    this.$el.find('.add-comment').show();
    this.$el.find('textarea.content').removeClass('error');
  },
  submit_comment: function (e) {
    e.preventDefault();
    var $comment_form = this.$el.find(e.target).closest('form.comment-form'),
      $comment_field = $comment_form.find('textarea.content'),
      $comment_button = $comment_form.find('button.add-comment'),
      $comment_list = this.$el.find('ul.comments'),
      $comment_count = this.$el.find(".comment .count"),
      comment = $comment_field.val();

    if ($comment_button.hasClass('loading')) return true;

    if (!comment || !comment.trim()) {
      $comment_field.addClass('error');
    } else {

      $comment_button.addClass('loading');
      var comment_data = $comment_form.serialize();

      $.ajax({
        method: 'POST',
        url: '/api/comments/',
        data: comment_data,
        dataType: 'json'
      }).done(function (data, textStatus, jqXHR) {
        $comment_list.append(data.html);
        $comment_count.html(data.total_comment);
        $comment_field.val('');
        ga('send','content_generation','submit_review',window.location.href); //Google Analytics Event Tracking

      }).fail(function (jqXHR, textStatus, errorThrown) {

        $comment_field.addClass('error');

      }).complete(function () {

        $comment_button.removeClass('loading');

      });
    }
  },
  flag_comment: function (e) {
    e.preventDefault();
    var comment_id = $(e.target).attr('data-comment');

    bootbox.confirm("Are you sure you want to report this review?", function (result) {
      if (result) {
        $.ajax({
          url: '/api/commentflag/',
          method: 'POST',
          data: {
            'comment_id': comment_id
          }
        });
      }
    });
  },
  parseAddress: function () {
    var self = this;
    self.$el.find('.pin-neighborhood').hide();
    self.$el.find(".pin-address").hide();

    var formattedAddress = self.model.get("l_address");

    
    if (!formattedAddress) {
      return false;
    }

    self.geoCoder.geocode({address: formattedAddress}, function (results, status) {
      if (status == google.maps.GeocoderStatus.OK && results.length) {
        var addressComponents = results[0].address_components;
        var hashedAddress = _.indexBy(addressComponents, function (o) {
          return o.types.join('-')
        });
        var html = '', htmlPart;

        var row2Data = ['street_number', 'route', 'subpremise'];
        var row3Data = ['locality-political', 'administrative_area_level_1-political', 'postal_code','country-political'];
       

        if (!hashedAddress['street_number'] || !hashedAddress['route'] ) {
          if (hashedAddress['natural_feature']){
            html += '<div>' + hashedAddress['natural_feature']['long_name'] + '</div>';
          } else if (hashedAddress['establishment']) {
            html += '<div>' + hashedAddress['establishment']['short_name'] + '</div>';
          } else if (hashedAddress['point_of_interest']) {
            html += '<div>' + hashedAddress['point_of_interest']['short_name'] + '</div>';
          }
        }

        htmlPart = _getFormattedAddress(hashedAddress, row2Data, ' ');
        if (htmlPart) {
          html += htmlPart;
        }

        if (!hashedAddress['locality-political']) { row3Data[0] = 'administrative_area_level_2-political'; }
        htmlPart = _getFormattedAddress(hashedAddress, row3Data, ', ');
        if (htmlPart) {
          html += htmlPart;
        }
        self.$el.find(".pin-address").show().html(html);
        
        var storedNeighborhood = self.model.get("l_neighborhood");
        if (!storedNeighborhood) {
          var neighborhood;
          if (hashedAddress['neighborhood-political']) {
            neighborhood = hashedAddress['neighborhood-political']['short_name'];
          } else if (hashedAddress['locality-political']) {
            neighborhood = hashedAddress['locality-political']['long_name'];
          } else if (hashedAddress['administrative_area_level_2-political']) {
            neighborhood = hashedAddress['administrative_area_level_2-political']['long_name'];
          } else if (hashedAddress['administrative_area_level_1-political']) {
            neighborhood = hashedAddress['administrative_area_level_1-political']['long_name'];
          }
          
          if (neighborhood) {
            self.$el.find('.pin-neighborhood').show().find('span').html(neighborhood);
          }
        } else {
            self.$el.find('.pin-neighborhood').show().find('span').html(storedNeighborhood);
        }
      }
    });

    function _getFormattedAddress(addrComponents, fields, sep) {
      var values = [], fmt='short_name', value;
      fields.forEach(function (field) {
        if (addrComponents.hasOwnProperty(field)) {
          if (field === 'subpremise') {
            value = '#' + addrComponents[field][fmt];
          } else if (field === 'locality-political' || field === 'administrative_area_level_2-political') {
            value = addrComponents[field]['long_name'];
          } else {
            value = addrComponents[field][fmt];
          }
          values.push(value);
        }
      });
      if (!values.length) {
        return null
      }
      return '<div>' + values.join(sep) + '</div>';
      
    }
  }
});


var AjaxForm = Backbone.View.extend({
  tagName: 'form',

  initialize: function (options) {
    this.$('button[type=submit]').click(_.bind(this.submit, this));
    if (this.model) this.listenTo(this.model, "change", _.bind(this.update, this));
    this.method = this.$el.attr('method');
    this.update();
    this.validation = options.validation;
    this.onSuccess = options.onSuccess;
    this.onErrors = options.onErrors;
  },

  update: function () {
    this.action = this.$el.attr('action');
    if (!this.action && this.model) this.action = this.model.url();
  },

  resetErrors: function () {
    this.$('.form-group').removeClass('has-error');
    this.$('.error').html('');
    this.$('.alert-form.alert-danger').addClass('hide');
  },

  handleErrors: function (errors) {

    _(errors).each(_.bind(function (value, key) {
      if (key == "__all__") {
        this.$(".alert-form.alert-danger,.form-error").html(value[0]).removeClass("hide");
      }

      var control = this.$('[name=' + key + ']');

      var error = control.nextAll('.error');
      if (error) error.html(value);

      var formGroup = control.parent('.form-group');
      if (formGroup) formGroup.addClass('has-error');
    }, this));
    if (this.onErrors) this.onErrors();
  },

  submit: function (e) {
    e.preventDefault();
    this.resetErrors();
    this.$el.addClass('loading');

    // client-side validation
    if (this.validation) {
      var errors = this.validation(this.$el);
      if (errors && _.size(errors) > 0) {
        this.handleErrors(errors);
        this.$el.removeClass('loading');
        return;
      }
    }

    var data = this.$el.serialize();
    $.ajax({
      url: this.action,
      data: data,
      type: this.method
    }).done(_.bind(function (data, textStatus, jqXHR) {
      this.$el.removeClass('loading');
      this.resetErrors();
      if (this.model) {
        this.model.set(data);
      }
      if (this.onSuccess) this.onSuccess(data);
    }, this)).fail(_.bind(function (jqXHR, textStatus, errorThrown) {
      this.$el.removeClass('loading');
      this.resetErrors();
      // Validation error
      if (jqXHR.status == 400) {
        var errors = $.parseJSON(jqXHR.responseText);
        this.handleErrors(errors);

        // Server error
      } else {
        var serverError = this.$('.server-error,.alert-form.alert-danger,.form-error');
        // Timeout
        if (jqXHR.statusText == 'timeout') {
          if (serverError) serverError.html('Server not responding.');
          // Something else
        } else {
          if (serverError) serverError.html('Server error. Please try again.');
          console.log(jqXHR);
        }
      }
    }, this));
    return false;
  }
});

var NewPinModal = Backbone.View.extend({
  ajaxUploadFinished: true,
  isPlaceSelected: false,
  el: $('#newPinModal'),
  defaultBounds: new google.maps.LatLngBounds(
    new google.maps.LatLng(47.4955511, -122.43590849999998), // SW
    new google.maps.LatLng(47.734145, -122.2359032) // NE
  ),
  events: {
    'click a.geolocation': 'locate'
  },

  initialize: function (options) {
    var view = this;
    this.$('.preview').hide();
   
    this.$geolocation = this.$('.geolocation');
    this.$el.on('hidden.bs.modal', _.bind(this.reset, this));
    this.$('a[href=#newPinModal-submit-title]').click(_.bind(this.submitTitle, this));
    this.$('a[href=#newPinModal-submit-location]').click(_.bind(this.submitLocationForm, this));
    this.$('form').submit(_.bind(this.trySubmitForm, this));
    this.$('.preview img.image').load(_.bind(this.onPreviewLoad, this));
    this.$('form input[name=image]').change(_.bind(this.loadPreview, this));
    this.$("form input[name=image_url]").on("input", _.bind(this.uploadUrl, this));

    this.$('a[href^=#newPinModal-submit-image]').click(_.bind(this.submitImage, this));
    this.$('input#id_tags').tagsinput({
      confirmKeys: [44]
    });

    this.$('form input[name=title]').keyup(function () {
      var length = $(this).val().length;
      if (length >= 150) {
        $('.alert-title-length').removeClass("hide");
      }
      $('.alert-title-length').html("Maximum title length is 200. Your title has <b>" + length + "</b> characters.");
    });

    // Toggle hike details
    this.$('form select[name=category]').change(function () {
      view.$('.hike-details').toggle($('option:selected', this).data('is-hike') == 'True');
    }).trigger('change');

    // Submit by enter
    this.$('.tab-pane').keypress(function (e) {
      if (e.which == 13) {
        $('.submit', this).click();
        e.preventDefault();
      }
    });

    if (options && options.address) new google.maps.Geocoder().geocode({
      address: options.address
    }, function (results) {
      if (results.length) {
        var geometry = results[0].geometry;
        var bounds = new google.maps.LatLngBounds();
        if (geometry.viewport) {
          bounds.extend(new google.maps.LatLng(geometry.viewport.getNorthEast().lat(), geometry.viewport.getNorthEast().lng()));
          bounds.extend(new google.maps.LatLng(geometry.viewport.getSouthWest().lat(), geometry.viewport.getSouthWest().lng()));
        } else {
          bounds.extend(new google.maps.LatLng(geometry.location.lat(), geometry.location.lng()));
        }
        view.defaultBounds = bounds;
      }
    });
  },

  geocodePosition: function (pos) {
    var view = this;
    geocoder = new google.maps.Geocoder();
    geocoder.geocode({
      latLng: pos
    }, function (results, status) {
      if (status == google.maps.GeocoderStatus.OK) {
        if (results[0]) {
          view.marker.setTitle(results[0].formatted_address);
          this.$('#newPinModal-tab-map input.input-address').val(results[0].formatted_address);
          var addressComponents = results[0].address_components;
          var hashedAddress = _.indexBy(addressComponents, function (o) {
            return o.types.join('-')
          });

          var neighborhood;
          if (hashedAddress['neighborhood-political']) {
            neighborhood = hashedAddress['neighborhood-political']['short_name'];
          } else if (hashedAddress['locality-political']) {
            neighborhood = hashedAddress['locality-political']['long_name'];
          } else if (hashedAddress['administrative_area_level_2-political']) {
            neighborhood = hashedAddress['administrative_area_level_2-political']['long_name'];
          } else if (hashedAddress['administrative_area_level_1-political']) {
            neighborhood = hashedAddress['administrative_area_level_1-political']['long_name'];
          }
          view.$(".hidden-neighborhood").val(neighborhood);
        }
      }
    })
    
  },
  
  
  geocodeNeighborhood: function (pos) {
    var view = this;
    geocoder = new google.maps.Geocoder();
    geocoder.geocode({
      latLng: pos
    }, function (results, status) {
      if (status == google.maps.GeocoderStatus.OK) {
        if (results[0]) {
          view.marker.setTitle(results[0].formatted_address);
          var addressComponents = results[0].address_components;
          var hashedAddress = _.indexBy(addressComponents, function (o) {
            return o.types.join('-')
          });

          var neighborhood;
          if (hashedAddress['neighborhood-political']) {
            neighborhood = hashedAddress['neighborhood-political']['short_name'];
          } else if (hashedAddress['locality-political']) {
            neighborhood = hashedAddress['locality-political']['long_name'];
          } else if (hashedAddress['administrative_area_level_2-political']) {
            neighborhood = hashedAddress['administrative_area_level_2-political']['long_name'];
          } else if (hashedAddress['administrative_area_level_1-political']) {
            neighborhood = hashedAddress['administrative_area_level_1-political']['long_name'];
          }
          view.$(".hidden-neighborhood").val(neighborhood);
        }
      }
    })
    
  },
    
  

  locate: function (e) {
    e.preventDefault();
    if (!this.$geolocation.hasClass('disabled')) {
      this.$geolocation.addClass('disabled');
      geolocator.locate();
    }
  },

  initMap: function (modal) {
    var view = this;
    var map = this.map;
    if (this.map) {
      this.map.fitBounds(this.defaultBounds);
      return;
    } else {
      this.map = new google.maps.Map(this.$('#map-canvas').get(0), {
        mapTypeId: google.maps.MapTypeId.ROADMAP
      });
      geolocator.on('locate', function (location) {
        this.marker.setPosition(location);
        google.maps.event.trigger(this.marker, 'dragend');
        this.map.panTo(location);
        this.$geolocation.removeClass('disabled').addClass('on');
      }, this);
    }

    this.marker = new google.maps.Marker({
      map: this.map,
      draggable: true
    });
    this.map.fitBounds(this.defaultBounds);

    this.$inputAddress = this.$('#newPinModal-tab-map input.input-address');
    this.searchBox = new google.maps.places.SearchBox(this.$inputAddress.get(0));

    google.maps.event.addListener(this.searchBox, 'places_changed', function () {
      var places = view.searchBox.getPlaces();
      if (places.length == 0) return;
      var bounds = new google.maps.LatLngBounds();
      if (places.length > 0) {
        var place = places[0];
        if (!place.geometry) return;
        view.marker.setPosition(place.geometry.location);
        view.marker.setTitle(place.name);

        if (place.geometry && place.geometry.viewport) {
          bounds.extend(new google.maps.LatLng(place.geometry.viewport.getNorthEast().lat(), place.geometry.viewport.getNorthEast().lng()));
          bounds.extend(new google.maps.LatLng(place.geometry.viewport.getSouthWest().lat(), place.geometry.viewport.getSouthWest().lng()));
        } else {
          bounds.extend(new google.maps.LatLng(place.geometry.location.lat(), place.geometry.location.lng()));
        }
      }

      if (bounds.getNorthEast().equals(bounds.getSouthWest())) {
        var extendPoint1 = new google.maps.LatLng(bounds.getNorthEast().lat() + 0.004, bounds.getNorthEast().lng() + 0.004);
        var extendPoint2 = new google.maps.LatLng(bounds.getNorthEast().lat() - 0.004, bounds.getNorthEast().lng() - 0.004);

        bounds.extend(extendPoint1);
        bounds.extend(extendPoint2);
      }
      view.map.fitBounds(bounds);
    });
    google.maps.event.addListener(view.map, 'bounds_changed', function () {
      var bounds = view.map.getBounds();
      view.searchBox.setBounds(bounds);
      view.$('.hidden-bounds').val(JSON.stringify({
        ne: {
          lat: bounds.getNorthEast().lat(),
          lng: bounds.getNorthEast().lng()
        },
        sw: {
          lat: bounds.getSouthWest().lat(),
          lng: bounds.getSouthWest().lng()
        }
      }));
    });
    google.maps.event.addListener(view.map, 'click', function (event) {
      view.marker.setPosition(event.latLng);
      view.geocodePosition(view.marker.getPosition());
    });
    
    google.maps.event.addListener(view.marker, 'dragend', function () {
      view.geocodePosition(view.marker.getPosition());
    });
    google.maps.event.addListener(view.marker, 'position_changed', function () {
      view.geocodeNeighborhood(view.marker.getPosition());
      view.$(".hidden-place").val(JSON.stringify({
        lat: view.marker.getPosition().lat(),
        lng: view.marker.getPosition().lng()
      }));
      view.isPlaceSelected = true;
    });
    

    
  },

  reset: function () {
    this.$('.tab-pane').removeClass('active');
    this.$('#newPinModal-tab-title').addClass('active');

    this.$('.form-group').removeClass('has-error');
    this.$('form input[name=description]').val('');
    this.$('form input[name=tags]').tagsinput('removeAll');

    this.$('a[href=#newPinModal-submit-image]').removeClass('disabled');

    this.$('form input[name=image]').prop('disabled', false).val('');
    this.$('form input[name=title]').val('');
    this.$('form input[name=site_url]').val('');
    this.$('.preview').removeClass('loading').hide().find("img.image").attr('src', '');
    this.$('form input[name=image_url]').val('');

    this.$('form a[href=#newPinModal-location-location]').removeClass("disabled");
    this.$('form').find('.progress').addClass("hide");
    this.resetErrorHandler();
    this.isPlaceSelected = false;
    this.$('form').find('.progress').addClass('hide');

    this.$('form .phone-number input').val('');
    this.$('form .hike-details input').val('');
    this.$('form select[name=category]').val(this.$('form select[name=category] option:first').val()).change();
    this.$("form #newPinModal-tab-map .input-address").val('');
  },

  resetErrorHandler: function () {
    this.$('#newPinModal-error-holder').html(null).addClass('hide').css('display', 'inline');
  },

  showErrorMessages: function (errors, timeToShow) {
    timeToShow = a = typeof a !== 'undefined' ? a : 3000;
    var view = this;
    if (Object.prototype.toString.call(errors) !== '[object Array]') {
      errors = [errors];
    }
    var $errorHolder = $('#newPinModal-error-holder');
    errors.forEach(function (error) {
      $errorHolder.append(_.template(
        $('#newPinModal-error-template').html(), {
          'type': 'danger',
          'message': error
        }));
    });
    $errorHolder.removeClass('hide');
    if (timeToShow !== 0) {
      var interval = setInterval(function () {
        $errorHolder.fadeOut('slow', function () {
          view.resetErrorHandler();
        });
        clearInterval(interval);
      }, timeToShow);
    }
  },

  resetWithErrors: function (errors, timeToShow) {
    timeToShow = a = typeof a !== 'undefined' ? a : 3000;
    this.reset();
    this.showErrorMessages(errors, timeToShow);
  },

  loadPreview: function () {
    this.$('.preview').addClass('loading').show();
    var url = this.$('form input[name=image_url]').val();
    var input = this.$('form input[name=image]').get(0);
    if (input.files && input.files[0]) {
      var reader = new FileReader();
      reader.onload = _.bind(function (e) {
        this.$('.preview img.image').attr('src', e.target.result);
      }, this);
      reader.readAsDataURL(input.files[0]);
    } else if (url) {
      this.$('.preview img.image').attr('src', url);
    }
  },

  onPreviewLoad: function () {
    this.$('.preview').removeClass('loading');
  },

  shake: function (field) {
    var $field = this.$(field);
    $field.addClass('has-error');
    $(':input', $field).focus();
    this.$('.modal-content').effect('shake');
    return false;
  },

  submitTitle: function () {
    var $form = this.$('form');
    this.$('#newPinModal-tab-title .form-group').removeClass('has-error');
    ga('send','content_generation','add_location',window.location.href);  //Google Analytics Event Tracking

    var title = $form.find('input[name=title]').val().trim();
    if (!title) return this.shake('.field-title');

    var url = $form.find('input[name=site_url]').val().trim();
    if (url && !this.validateURL(url)) return this.shake('.field-url');

    if (typeof this.$('.field-category select').val() == 'undefined' || this.$('#newPinModal-tab-title select').val() == null) this.shake('.field-category');

    if (this.$('select[name=category] option:selected').data('is-hike') == 'True') {
      var hikeDetail = {};
      if (typeof this.$('select.trail-length').val() == 'string' && this.$('input.trail-length').val().trim() !== "") {
        if (!this.isNumber(this.$('input.trail-length').val().trim())) {
          return this.shake('.field-trail-length');
        } else {
          hikeDetail["trail"] = {
            'amount': this.$('input.trail-length').val().trim(),
            'unit': this.$('select.trail-length').val()
          }
        }
      }
      if (typeof this.$('select.elevation-gain').val() == 'string' && this.$('input.elevation-gain').val().trim() !== '') {
        if (!this.isNumber(this.$('input.elevation-gain').val().trim())) {
          return this.shake('.field-elevation-gain');
        } else {
          hikeDetail['elevation'] = {
            'amount': this.$('input.elevation-gain').val().trim(),
            'unit': this.$('select.elevation-gain').val()
          }
        }
      }
      if (typeof this.$('select.highest-point').val() == 'string' && this.$('input.highest-point').val().trim() !== "") {
        if (!this.isNumber(this.$('input.highest-point').val().trim())) {
          return this.shake('.field-highest-point');
        } else {
          hikeDetail['highest'] = {
            'amount': this.$('input.highest-point').val().trim(),
            'unit': this.$('select.highest-point').val()
          }
        }
      }
      this.$('input.hike-detail').val(JSON.stringify(hikeDetail));
    }

    var phoneNumber = {
      'area_code': this.$('input#area-code').val().trim(),
      'exchange_code': this.$('input#exchange-code').val().trim(),
      'number': this.$('input#phone-number').val().trim()
    }
    if (phoneNumber.area_code && phoneNumber.exchange_code && phoneNumber.number) {
      this.$('input.phone-number').val(phoneNumber.area_code + phoneNumber.exchange_code + phoneNumber.number);
    } else if (phoneNumber.area_code || phoneNumber.exchange_code || phoneNumber.number) {
      return this.shake('.phoneNumber');
    }

    this.$('form').find('a[href=#newPinModal-submit-map]').removeClass("disabled");
    $(this.$('a[href^=#newPinModal-tab-map]')).tab('show');
    this.initMap();

    return false;
  },

  submitLocationForm: function () {
    var $form = this.$('form');
    if (!this.isPlaceSelected) {
      this.$('.modal-content').effect("shake");
      return false;
    }
    if (this.$('#newPinModal-tab-map input.input-address').val().trim() == "") {
      this.$('.modal-content').effect("shake");
      return false;
    }
    $(this.$('a[href^=#newPinModal-tab-image]')).tab('show');
    return false;
  },

  submitImage: function (e) {
    var view = this;
    var $submit = this.$('a[href=#newPinModal-submit-image]');
    if ($submit.hasClass('disabled')) return false;
    var image = this.$('form input[name=image]').val();
    var image_url = this.$('form input[name=image_url]').val();
    var file_max_size = parseInt($('#file-max-size').val());
    var file_too_big_error_msg = $('#file-too-big-error-msg').val();
    var unknown_error_msg = $('#unknown-error-msg').val();
    var format_unsupported_error_msg = $('#format-unsupported-error-msg').val();
    var supported_formats_list = $('#supported-formats-list').val().toLowerCase().split(',');

    if (!image && !image_url) {
      this.$('.modal-content').effect('shake');
      return false;
    }

    if (!!image && !!window.FileReader && this.$('form input[name=image]')[0].files[0].size > file_max_size) {
      view.showErrorMessages(file_too_big_error_msg, 5000);
      return false;
    }

    var extension = function (filename) {
      var i = filename.length;
      while (i >= 0 && filename.charAt(i) !== '.') {
        --i;
      }
      if (i < 0) return '';
      return filename.substr(i + 1).toLowerCase();
    }(image ? image : image_url);
    if ($.inArray(extension, supported_formats_list) === -1) {
      view.showErrorMessages(format_unsupported_error_msg, 5000);
      return false;
    }

    var action = this.$("form").attr("action");
    var upload = this.$("form").data("image-upload-api");

    //swap action just for image upload
    this.$("form").get(0).setAttribute("action", upload);

    this.ajaxUploadFinished = false;
    this.$("form").ajaxSubmit({
      timeout: 0,
      success: _.bind(function (response) {
        view.$('form').find('.progress').addClass("hide");
        // set TemporaryImage id and disable image input (file already uploaded)
        this.$("#temp_image").val(response);
        this.$("form input[name=image]").prop("disabled", true);
        view.ajaxUploadFinished = true;
        view.$('form').submit();
      }),
      error: _.bind(function (error) {
        var errorText = error.responseText;
        view.$('form').find('.progress').addClass("hide");
        view.$('form').find('a[href=#newPinModal-submit-image]').removeClass("disabled");
        view.$('form').find('a[href=#newPinModal-finish]').removeClass("disabled");

        // filter out possible non-printable characters
        errorText = errorText.replace(/[\x80-\xFF]/g, '');
        try {
          var errorDict = $.parseJSON(errorText);
          var errors = [];
          for (key in errorDict) {
            var value = errorDict[key];
            if (Object.prototype.toString.call(value) === '[object Array]') {
              errors = errors.concat(value);
            } else {
              errors.push(value);
            }
          }
          view.showErrorMessages(errors, 3000);
        } catch (e) {
          if (error.status === 413) {
            // file too large
            view.showErrorMessages(3000);
          } else {
            errorText = unknown_error_msg + ' ' + errorText;
            view.showErrorMessages(0);
          }
        }
      })
    });

    // set back the original action
    this.$("form").get(0).setAttribute("action", action);
    this.$('form').find('.progress').removeClass("hide");
    $submit.addClass('disabled');
    return false;
  },

  validateURL: function (textval) {
    var urlregex = new RegExp(
      "([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&amp;%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&amp;%\$#\=~_\-]+))*$");
    return urlregex.test(textval);
  },
  isNumber: function (n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  },

  trySubmitForm: function () {
    var $form = this.$('form');
    var view = this;

    if (this.ajaxUploadFinished) {
      return true;
    }

    // submit the form when upload is finished
    var interval = setInterval(_.bind(function () {
      if (view.ajaxUploadFinished) {
        clearInterval(interval);
        $form.submit();
      }
    }), 300);

    return false;
  },

  uploadUrl: function () {
    this.loadPreview();
  }
});


var geolocator = new (Backbone.Model.extend({

  initialize: function (attributes, options) {
    this.userAgent = navigator.userAgent;
    var view = this;
    this._error = function () {
      console.error('geolocation', arguments);
      view.trigger('error', arguments);
    };
  },

  isAvailable: function () {
    return 'geolocation' in navigator
  },

  locate: function () {
    if (!this.isAvailable()) return;
    var view = this;
    navigator.geolocation.getCurrentPosition(function (position) {
      view.trigger('locate', new google.maps.LatLng(position.coords.latitude, position.coords.longitude));
    }, this._error, {
      maximumAge: Infinity
    });
  },

  watch: function () {
    if (!this.isAvailable()) return false;
    this.unwatch();
    var view = this;
    this.watchID = navigator.geolocation.watchPosition(function (position) {
      view.trigger('watched', new google.maps.LatLng(position.coords.latitude, position.coords.longitude));
    }, this._error);
    return true;
  },

  unwatch: function () {
    if (this.watchID) {
      navigator.geolocation.clearWatch(this.watchID);
      return true;
    }
    return false;
  }
}));


var LocalFilterForm = Backbone.View.extend({

  el: '.media form.filters',

  events: {
    'change :input': 'onChange',
    'click a.geolocation': 'locate'
  },

  initialize: function () {
    this.params = {};
    this.starterT = _.template($('script.pinboard-starter').html());
    this.$geocomplete = this.$(':input[name=geocomplete]');
    this.$geocomplete.geocomplete({
      details: this.$el,
      location: this.$geocomplete.val()
    });

    this.ignoreGeocomplete = this.options.ignoreGeocomplete || false;

    this.$geolocation = this.$('.geolocation');
    this.$geolocation.toggle(geolocator.isAvailable());
    geolocator.on('locate', function (location) {
      this.$('input[name=lat]').val(location.lat());
      this.$('input[name=lng]').val(location.lng()).change();
      var view = this;
      new google.maps.Geocoder().geocode({
        location: location
      }, function (results, status) {
        if (results) view.$('[name=geocomplete]').val(results[0].formatted_address);
        view.$geolocation.removeClass('disabled').addClass('on');
      });
    }, this);
  },

  onChange: function (e) {
    if (e && ($(e.target).attr('name') == 'geocomplete') && this.ignoreGeocomplete) return;
    var view = this;
    if (this.timeoutID != null) {
      window.clearTimeout(this.timeoutID);
      this.timeoutID = null;
    }
    this.timeoutID = window.setTimeout(function () {
      view.$(':input').each(function () {
        var control = $(this);
        var key = control.attr('name'),
          value = control.val();
        view.params[key] = value
      });
      view.refresh();
    }, 1000);
  },

  refresh: function () {
    var view = this;
    view.trigger('refresh');
    if (this.xhr != null) {
      this.xhr.abort();
    }
    lazyReset();
    var q = '?part_number=0&' + $.param(this.params);
    $('.pinboard-container').empty().append(this.starterT({
      q: q
    }));
    this.xhr = lazyStart(function () {
      // bind pinboard to modals
      $('.pinboard .pin a.zoom').click(function (e) {
        e.preventDefault();
        var id = $(this).data('id');
        pin.set({
          id: id
        });
        pinModal.open();
      });
      view.trigger('lazyimg');
    });
  },

  locate: function (e) {
    e.preventDefault();
    if (!this.$geolocation.hasClass('disabled')) {
      this.$geolocation.addClass('disabled');
      geolocator.locate();
    }
  }
});


/** @constructor */
function ClusterMarker(latlng, count, map, ids, bounds) {
  this.position = latlng;
  this.map = map;
  this.count = count;
  this.ids = ids;
  this.bounds = bounds;
  if (count > 10000) this._countGroup = 10000;
  else if (count > 1000) this._countGroup = 1000;
  else if (count > 100) this._countGroup = 100;
  else if (count > 1) this._countGroup = 10;
  this.background = "url('" + this.imagesUrlPrefix + String(this._countGroup) + "_.png')";
  this.backgroundActive = "url('" + this.imagesUrlPrefix + String(this._countGroup) + ".png')";
  // Define a property to hold the image's div. We'll
  // actually create this div upon receipt of the onAdd()
  // method so we'll leave it null for now.
  this._div = null;
  // Explicitly call setMap on this overlay.
  this.setMap(map);
};
ClusterMarker.prototype = new google.maps.OverlayView();

ClusterMarker.prototype.onAdd = function () {
  this.size = this._images[this._countGroup];

  var div = document.createElement('div');
  div.style.position = 'absolute';
  div.style.width = this.size + "px";
  div.style.height = this.size + "px";
  div.style.textAlign = "center";
  div.style.lineHeight = this.size + "px";
  div.style.background = this.background;

  var labelDiv = document.createElement('div');
  labelDiv.className = "clusterMarkerText cluster-" + this._countGroup;
  labelDiv.textContent = this.count;
  div.appendChild(labelDiv);

  this._div = div;

  // Add the element to the "overlayMouseTarget" pane for making clicks possible.
  this.getPanes().overlayMouseTarget.appendChild(div);

  // Add a listener - we'll accept clicks anywhere on this div, but you may want
  // to validate the click i.e. verify it occurred in some portion of your overlay.
  var marker = this;
  google.maps.event.addDomListener(div, 'click', function () {
    google.maps.event.trigger(marker, 'click');
  });

  var bg = this.background;
  var bgActive = this.backgroundActive;
  google.maps.event.addDomListener(div, 'mouseover', function () {
    div.style.background = bgActive;
  });
  google.maps.event.addDomListener(this, 'mouseover', function () {
    div.style.background = bgActive;
  });
  google.maps.event.addDomListener(div, 'mouseout', function () {
    div.style.background = bg;
  });
  google.maps.event.addDomListener(this, 'mouseout', function () {
    div.style.background = bg;
  });
};
ClusterMarker.prototype._images = {
  // count : size(px)
  10: 30,
  100: 40,
  1000: 50,
  10000: 60
};
ClusterMarker.prototype.imagesUrlPrefix = '/static/img/markers/';

ClusterMarker.prototype.draw = function () {
  // Transform the center into pixel position on map
  var pos = this.getProjection().fromLatLngToDivPixel(this.position);
  // Resize the image's div to fit the indicated dimensions.
  var div = this._div;

  var xOffset = this.size / 2;
  var yOffset = this.size / 2;

  var x = pos.x - xOffset;
  var y = pos.y - yOffset;

  div.style.left = x + 'px';
  div.style.top = y + 'px';
};

// The onRemove() method will be called automatically from the API if
// we ever set the overlay's map property to 'null'.
ClusterMarker.prototype.onRemove = function () {
  this._div.parentNode.removeChild(this._div);
  this._div = null;
};

var $filterToggle = $('.local-filter-toggle');
$filterToggle.click(function () {
  $filterToggle.toggleClass('active');
  $('.media').toggleClass('hidden');
});

var MapView = Backbone.View.extend({
  el: '#map-view',
  events: {
    'change form.filters:input': 'onFilterChange'
  },

  markerImage: new google.maps.MarkerImage(
    '/static/img/markers/pin_.png',
    new google.maps.Size(22, 22),
    new google.maps.Point(0, 0),
    new google.maps.Point(11, 11)),

  markerImageActive: new google.maps.MarkerImage(
    '/static/img/markers/pin.png',
    new google.maps.Size(22, 22),
    new google.maps.Point(0, 0),
    new google.maps.Point(11, 11)),

  userAgent: navigator.userAgent,

  locationMarker: new google.maps.Marker({
    flat: true,
    icon: new google.maps.MarkerImage(
      '/static/img/markers/geolocation.png',
      null, // size
      null, // origin
      new google.maps.Point(11, 11), // anchor (move to center of marker)
      new google.maps.Size(22, 22) // scaled size (required for Retina display icon)
    ),
    optimized: false,
    title: 'This is you',
    visible: true,
    clickable: false
  }),

  initialize: function (options) {
    var view = this;
    var listItemWidth = options.listItemWidth || 286;
    var listItemPadding = options.listItemPadding || 5;
    var listWidthRatio = options.listWidthRatio || 0.6;
    var listScrollBarCompensation = options.listScrollBarCompensation || 10;

    // List will take up to `listWidthRatio` of width but to fit grid best
    var $map = this.$('#map');
    var $list = this.$('#map-pins');
    var $navbar = $('.navbar');
    var $media = $('#wrap .media');
    var $window = $(window);

    $window.resize(function () {
      var viewHeight = $window.height() - $navbar.outerHeight(); // - $footer.outerHeight();

      if ($window.width() > 479) {
        if ($window.width() > 767) {
          viewHeight -= $media.outerHeight();
          $('.list-filter-toggle').removeClass('active');
          $('.media').removeClass('hidden');
        }

        $map.height(viewHeight);
        $list.height(viewHeight);
        var width = $window.width();
        var maxListWidth = width * listWidthRatio;
        var gridSize = Math.floor((maxListWidth - listItemPadding) / (listItemWidth + listItemPadding));
        var listWidth = gridSize * (listItemWidth + listItemPadding) + listItemPadding + listScrollBarCompensation;
        $list.width(listWidth);
        $map.width(width - listWidth);
      } else {
        $media.addClass('hidden');
        $map.height(Math.floor(viewHeight * .4));
        $list.height(Math.ceil(viewHeight * .6));
        $map.width('100%');
        $list.width('100%');
      }
    }).trigger('resize');

    if (!options) options = {};

    view.map = new google.maps.Map($map.get(0), {
      zoom: options.zoom || 3,
      scrollwheel: true,
      mapTypeId: google.maps.MapTypeId[options.mapTypeId || 'ROADMAP']
    });

    geolocator.on('locate', function (location) {
      view.locationMarker.setMap(view.map);
      view.locationMarker.setPosition(location);
      view.map.panTo(location);
      geolocator.watch();
    });

    geolocator.on('watched', function (location) {
      view.locationMarker.setPosition(location);
    });

    var filterForm = this.options.filterForm;
    if (filterForm) {
      google.maps.event.addListener(view.map, 'idle', function () {
        var bounds = view.map.getBounds();
        if (bounds) {
          filterForm.$(':input[name=left]').val(bounds.getSouthWest().lng());
          filterForm.$(':input[name=right]').val(bounds.getNorthEast().lng());
          filterForm.$(':input[name=top]').val(bounds.getNorthEast().lat());
          filterForm.$(':input[name=bottom]').val(bounds.getSouthWest().lat()).change(); // trigger!
        }
      });
    }

    google.maps.event.addListener(view.locationMarker, 'click', function () {
      view.map.setCenter(view.locationMarker.getPosition());
    });
    this.markers = [];
    this.pinIdToMarker = {};
    if (options.filterForm) {
      options.filterForm.on('refresh', _.bind(function () {
        this.extraParams = options.filterForm.params;
        this.refresh();
      }, this));
      options.filterForm.on('lazyimg', function () {
        $('ul.pinboard > li > a').each(function () {
          var $this = $(this);
          var marker = view.pinIdToMarker[$this.data('id')];
          $this.hover(function () {
              google.maps.event.trigger(marker, 'mouseover');
            },

            function () {
              google.maps.event.trigger(marker, 'mouseout');
            });
        });
      });
    }
  },

  drawMarker: function (cluster) {
    var marker;
    var center = new google.maps.LatLng(cluster.center.lat, cluster.center.lng);
    var count = cluster.ids.length;
    if (count > 1) {
      var sw = new google.maps.LatLng(cluster.bounds.sw.lat, cluster.bounds.sw.lng);
      var ne = new google.maps.LatLng(cluster.bounds.ne.lat, cluster.bounds.ne.lng);
      var bounds = new google.maps.LatLngBounds(sw, ne);
      var marker = new ClusterMarker(center, count, this.map, cluster.ids, bounds);
      marker.bounds = bounds;
    } else {
      var image = this.markerImage;
      var imageActive = this.markerImageActive;
      marker = new google.maps.Marker({
        position: center,
        map: this.map,
        animation: google.maps.Animation.DROP,
        icon: image,
        zIndex: 1000000
      });
      marker.pinId = cluster.ids[0];
      google.maps.event.addListener(marker, 'mouseover', function () {
        marker.setIcon(imageActive);
      });
      google.maps.event.addListener(marker, 'mouseout', function () {
        marker.setIcon(image);
      });
    }
    return marker;
  },

  clearMarkers: function () {
    for (var i = 0; i < this.markers.length; i++) {
      var marker = this.markers[i];
      marker.setMap(null);
    }
    this.markers = [];
    this.pinIdToMarker = {};
  },

  refresh: function () // -> jQuery XHR
  {
    var map = this.map;
    if (this.xhr != null) {
      this.xhr.abort();
    }
    var bounds = map.getBounds();
    this.xhr = $.post('/map/markers/', _.extend({}, this.extraParams || {}, {
      left: bounds.getSouthWest().lng(),
      top: bounds.getNorthEast().lat(),
      right: bounds.getNorthEast().lng(),
      bottom: bounds.getSouthWest().lat(),
      zoom: map.getZoom()
    })).done(_.bind(function (data) {
      this.clearMarkers();
      for (var i = 0, cluster; cluster = data.clusters[i]; i++) {
        var marker = this.drawMarker(cluster);
        for (var j = 0, id; id = cluster.ids[j]; j++) {
          this.pinIdToMarker[id] = marker;
        }
        if (marker instanceof ClusterMarker) {
          google.maps.event.addListener(marker, 'click', function () {
            map.fitBounds(this.bounds);
          });
        } else {
          google.maps.event.addListener(marker, 'click', function () {
            window.pin.set({
              id: this.pinId
            });
            window.pinModal.open();
          });
        }
        console.log('pushing');
        this.markers.push(marker);
      }
    }, this));
    return this.xhr;
  }
});

//Google Analytics Event Tracking -- mobile call 
$('#call-mobile').on('click', function() {
  ga('send','actionables','mobile_call',window.location.href); 
}); 

//Google Analytics Event Tracking -- directions click - mobile
$('#directions-mobile').on('click', function() {
  ga('send','actionables','directions_mobile',window.location.href); 
}); 
//Google Analytics Event Tracking -- directions click - desktop
$('#directions-desktop').on('click', function() {
  ga('send','actionables','directions_desktop',window.location.href); 
}); 

//Google Analytics Event Tracking -- website link click -mobile
$('#website-mobile').on('click', function() {
  ga('send','actionables','website_link_mobile',window.location.href); 
}); 

//Google Analytics Event Tracking -- website link click - desktop
$('#website-desktop').on('click', function() {
  ga('send','actionables','website_link_desktop',window.location.href); 
}); 

//Google Analytics Event Tracking -- click call to action button/deal - mobile
$('#action-mobile').on('click', function() {
  ga('send','actionables','call_to_action_link_desktop',window.location.href); 
}); 

//Google Analytics Event Tracking -- click call to action button/deal - desktop
$('#action-desktop').on('click', function() {
  ga('send','actionables','call_to_action_link_desktop',window.location.href); 
}); 







