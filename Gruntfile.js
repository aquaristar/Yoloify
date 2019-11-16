module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    watch: {
      css: {
        files: 'static/less/yoloify.less',
        tasks: ['shell::compress'],
        options: {
          livereload: true
        }
      }
    },
    shell: {
      compress: {
        options: {
          stdout: true
        },
        command: './manage.py compress --force'
      }
    }
  });

  // Load the plugin that provides the "uglify" task.
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-shell');

  // Default task(s).
  grunt.registerTask('default', ['uglify']);

};