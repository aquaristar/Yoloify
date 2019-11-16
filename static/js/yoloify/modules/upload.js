App.module('Gallery.Upload', function(Upload, App, Backbone, Mn, $, _) {
  Upload.startWithParent = false;
  Upload.views = [];

  //Model
  Upload.File = Backbone.Model.extend({
    state: "pending",

    /**
     * Start upload.
     *
     */
    start: function () {
      if (this.isPending()) {
        this.get('processor').submit();
        this.state = "running";

        // Dispatch event
        this.trigger('filestarted', this);
      }
    },

    /**
     * Cancel a file upload.
     *
     */
    cancel: function () {
      this.get('processor').abort();
      this.destroy();

      // Dispatch event
      this.state = "canceled";
      this.trigger('filecanceled', this);
    },

    /**
     * Notify file that progress updated.
     *
     */
    progress: function (data) {
      // Dispatch event
      this.trigger('fileprogress', this.get('processor').progress());
    },

    /**
     * Notify file that upload failed.
     *
     */
    fail: function (error) {
      // Dispatch event
      this.state = "error";
      this.trigger('filefailed', error);
    },

    /**
     * Notify file that upload is done.
     *
     */
    done: function (result) {
      // Dispatch event
      this.state = "error";
      this.trigger('filedone', result);
    },

    /**
     * Is this file pending to be uploaded ?
     *
     */
    isPending: function () {
      return this.getState() == "pending";
    },

    /**
     * Is this file currently uploading ?
     *
     */
    isRunning: function () {
      return this.getState() == "running";
    },

    /**
     * Is this file uploaded ?
     *
     */
    isDone: function () {
      return this.getState() == "done";
    },

    /**
     * Is this upload in error ?
     *
     */
    isError: function () {
      return this.getState() == "error" || this.getState == "canceled";
    },

    /**
     * Get the file state.
     *
     */
    getState: function () {
      return this.state;
    }
  });

  //Collection
  Upload.FileCollection = Backbone.Collection.extend({
    model: Upload.File
  }),

  //Views
  Upload.FileView = Mn.ItemView.extend({
    tagName: 'div',
    className: 'uploading-file clearfix',
    template: _.template($('#upload-manager-file').html()),

    initialize: function () {
      // Bind model events
      this.model.on('destroy', this.close, this);
      this.model.on('fileprogress', this.updateProgress, this);
      this.model.on('filefailed', this.hasFailed, this);
      this.model.on('filedone', this.hasDone, this);

      // In each case, update view
      this.model.on('all', this.update, this);
    },
    render: function () {
      $(this.el).html(this.template(this.computeData()));
      // Bind events
      this.bindEvents();
      // Update elements
      this.update();
      return this;
    },
    updateProgress: function (progress) {
      var percent = parseInt(progress.loaded / progress.total * 100, 10);
      var progressHTML = percent +' %';
      this.$el.find('.progress-bar').css('width', percent + '%').html(progressHTML);
    },
    hasFailed: function (error) {
      this.$el.find('.message').html('<i class="fa fa-remove"></i> ' + error).addClass('error').show();
    },
    hasDone: function (result) {
      this.$el.find('.message').html('<i class="fa fa-check"></i> Uploaded').addClass('success').show();
    },
    update: function () {
      var when_running = $('.progress', this.el),
        when_done = $('.message', this.el);

      if (this.model.isRunning()) {
        when_done.addClass('hidden');
        when_running.removeClass('hidden');
      } else if (this.model.isDone() || this.model.isError()) {
        when_running.addClass('hidden');
        when_done.removeClass('hidden');
      }
    },
    bindEvents: function () {
      var self = this;
      $('#btn-cancel', this.el).click(function(){
        self.model.cancel();
      });
    },
    computeData: function () {
      return _.extend(this.getHelpers(), this.model.get('data'));
    },
    getHelpers: function () {
      return {
        displaySize: function (bytes) {
          var sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
          if (bytes == 0) return '0 B';
          var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
          return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
        }
      }
    }
  });

  Upload.FilesView = Mn.CollectionView.extend({
    childView: Upload.FileView,
    tagName: 'div',
    className: 'upload-manager'
  });

  //Controller
  Upload.Controller = Mn.Controller.extend({
    initialize: function (options) {
      this.fileId = 0;
      this.maxFileLimit = 5;
      this.photos = options.photos;
      this.uploadUrl = options.url;
      this.fileCollection = new Upload.FileCollection();
      this.bindEvents();
    },
    show: function () {
      var filesView = new Upload.FilesView({
        collection: this.fileCollection
      });
      $('#upload-progress').html(filesView.render().el);

      //To clean up
      Upload.views.push(filesView);
    },
    bindEvents: function () {
      _.bindAll(this, 'addCallback', 'successCallback', 'progressCallback', 'failCallback');
      $('#fileUpload').fileupload({
        autoUpload: true,
        url: this.uploadUrl,
        dataType: 'json',
        acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
        maxFileSize: 25000000, // 25 MB
        singleFileUploads: false,
        add: this.addCallback,
        done: this.successCallback,
        progress: this.progressCallback,
        fail: this.failCallback
      });
    },
    addCallback: function (e, data) {
      var self = this;
      var fileCount = data.files.length;
      if (fileCount > self.maxFileLimit) {
        alert("At a time, you can upload maximum " + self.maxFileLimit + " files");
        return false;
      }
      data.uploadManagerFiles = [];
      _.each(data.files, function (fileData) {
        // Create the file object
        fileData.id = self.fileId++;
        var file = new Upload.File({
          data: fileData,
          processor: data
        });
        // Add file in data
        data.uploadManagerFiles.push(file);
        self.fileCollection.add(file);
      });
      data.submit();
    },
    successCallback: function (e, data) {
      e.preventDefault();
      var self = this;
      _.each(data.uploadManagerFiles, function (file) {
        file.done(data.result);
        self.photos.unshift(new App.Gallery.Photo(data.result));
      });
    },
    progressCallback: function (e, data) {
      e.preventDefault();
      _.each(data.uploadManagerFiles, function (file) {
        file.progress(data)
      });
    },
    failCallback: function (e, data) {
      e.preventDefault();
      _.each(data.uploadManagerFiles, function (file, index) {
        var error = "Unknown error";
        if (typeof data.errorThrown == "string") {
          error = data.errorThrown;
        } else if (typeof data.errorThrown == "object") {
          error = data.errorThrown.message;
        } else if (data.result) {
          if (data.result.error) {
            error = data.result.error;
          } else if (data.result.files && data.result.files[index] && data.result.files[index].error) {
            error = data.result.files[index].error;
          } else {
            error = "Unknown remote error";
          }
        }
        file.fail(error);
      });
    }
  });

  //Initializer
  Upload.addInitializer(function(options) {
    Upload.controller = new Upload.Controller({
      photos: options.photos,
      url: options.url
    });
    Upload.controller.show();
  });

  //Finalizer
  Upload.addFinalizer(function() {
    console.log("Clearing Goal.Upload ...");
    _.each(Upload.views, function (view) {
      view.destroy();
    });
    Upload.views = [];
    Upload.controller.destroy();
    delete Upload.controller;
  });
});