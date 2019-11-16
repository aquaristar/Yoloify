$(function() {
    $('#side-menu').metisMenu();
});

//Loads the correct sidebar on window load,
//collapses the sidebar on window resize.
// Sets the min-height of #page-wrapper to window size
$(function() {
    $(window).bind("load resize", function() {
        topOffset = 50;
        width = (this.window.innerWidth > 0) ? this.window.innerWidth : this.screen.width;
        if (width < 768) {
            $('div.navbar-collapse').addClass('collapse')
            topOffset = 100; // 2-row-menu
        } else {
            $('div.navbar-collapse').removeClass('collapse')
        }

        height = (this.window.innerHeight > 0) ? this.window.innerHeight : this.screen.height;
        height = height - topOffset;
        if (height < 1) height = 1;
        if (height > topOffset) {
            $("#page-wrapper").css("min-height", (height) + "px");
        }
    });
});

function getChartKeysLabels (element) {
    if (element === 'user-line-chart') {
        return [['total_new_users', 'total_active_users'], ['New Users', 'Active Users']];  
    }
    else if (element === 'goal-line-chart') {
        return [['total_goal_pin', 'total_goal_repin', 'total_goal_completed'], ['Goal Pins', 'Goal Repins', 'Goal Completed']];  
    }
    else if (element === 'location-line-chart') {
        return [['total_location_pin', 'total_location_repin', 'total_location_completed'], ['Total Places', 'Total Bookmarks', 'Total Been Here']];  
    }
}

function drawMorrisLine (data, element) {
    var codes = getChartKeysLabels(element);
    $('#' + element).html('');
    Morris.Line({
        element: element,
        data: data,
        xkey: 'usage_date',
        ykeys: codes[0],
        labels: codes[1],
        lineColors: ['#1caf9a','#FF0000', '#0909FF'],
        xLabels: "day"
    });
}

function fetchDailyUsageStats (start, end, callback) {
    var baseURL = '/stats/usage/daily/';
    var params = $.param({from_date: start, to_date: end});
    var fullURL = baseURL + '?' + params;

    $.getJSON(fullURL, callback);
}    

function fetchLastWeekDailyUsage(element) {
    var start = moment().subtract('days', 7).format('YYYY-MM-DD');
    fetchDailyUsageStats(start, null, function(data) {
        drawMorrisLine(data, element);
    });
}

function fetchLastMonthDailyUsage(element) {
    var start = moment().subtract('months', 1).format('YYYY-MM-DD');  
    fetchDailyUsageStats(start, null, function(data) {
        drawMorrisLine(data, element);
    }); 
}

function fetchLast3MonthDailyUsage(element) {
    var start = moment().subtract('months', 3).format('YYYY-MM-DD')
    fetchDailyUsageStats(start, null, function(data) {
        drawMorrisLine(data, element);
    });
}

function fetchAllTimeDailyUsage(element) {
    fetchDailyUsageStats(null, null, function(data) {
        drawMorrisLine(data, element);
    });
}

function fetchTotalUsageStats (start, end, callback) {
    var baseURL = '/stats/usage/total/';
    var params = $.param({from_date: start, to_date: end});
    var fullURL = baseURL + '?' + params;

    $.getJSON(fullURL, callback);
}    

function updateTotalUsageStats (data, element) {
    var element = element || 'usage-stats-total';
    $('#' + element + ' span.tlp-count').html(data.total_location_pin);
    $('#' + element + ' span.tlrp-count').html(data.total_location_repin);
    $('#' + element + ' span.tgc-count').html(data.total_goal_completed);
    $('#' + element + ' span.tlc-count').html(data.total_location_completed);
    $('#' + element + ' span.tl-count').html(data.total_likes);
    $('#' + element + ' span.tc-count').html(data.total_comments);
    $('#' + element + ' span.tnu-count').html(data.total_new_users);
    $('#' + element + ' span.tau-count').html(data.total_active_users);
}

function fetchTodayTotalUsage (element) {
    var start = moment().format('YYYY-MM-DD');
    fetchTotalUsageStats(start, null, function(data) {
        updateTotalUsageStats(data, element);
    });
}

function fetchLastWeekTotalUsage (element) {
    var start = moment().subtract('days', 7).format('YYYY-MM-DD');
    fetchTotalUsageStats(start, null, function(data) {
        updateTotalUsageStats(data, element);
    });
}

function fetchLastMonthTotalUsage (element) {
    var start = moment().subtract('months', 1).format('YYYY-MM-DD');  
    fetchTotalUsageStats(start, null, function(data) {
        updateTotalUsageStats(data, element);
    }); 
}

function fetchLast3MonthTotalUsage (element) {
    var start = moment().subtract('months', 3).format('YYYY-MM-DD')
    fetchTotalUsageStats(start, null, function(data) {
        updateTotalUsageStats(data, element);
    });
}

function fetchAllTimeTotalUsage (element) {
    fetchTotalUsageStats(null, null, function(data) {
        updateTotalUsageStats(data, element);
    });
}

