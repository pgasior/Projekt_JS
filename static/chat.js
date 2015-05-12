/**
 * Created by Piotrek on 2015-05-12.
 */
$(document).ready(function() {
    //if (!window.console) window.console = {};
    //if (!window.console.log) window.console.log = function() {};

    $("#messageform").live("submit", function() {
        newMessage($(this));
        return false;
    });
    $("#messageform").live("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this));
            return false;
        }
    });

    $("#message").select();
    updater.start();
});

window.onresize = function(event) {
    var scroll = false;
    if($("#inbox").scrollTop()==$("#inbox")[0].scrollHeight-$("#inbox").outerHeight()) {
        scroll=true;
    }
    fixHeight(scroll);
};

function newMessage(form) {
    var message = form.formToDict();
    if(form.find("input[type=text]").val()!="") {
        updater.socket.send(JSON.stringify(message));
    }
    form.find("input[type=text]").val("").select();
}

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    //console.log(fields);
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

function fixHeight(scroll) {

    $("#inbox").height($(window).height()-$("#messageform").outerHeight());
    if(scroll==true){
        $("#inbox").scrollTop($("#inbox")[0].scrollHeight);
    }

}

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/chatsocket";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            updater.showMessage(JSON.parse(event.data));
        }
    },

    showMessage: function(message) {
        var existing = $("#message" + message.id);
        if (existing.length > 0) return;
        var node = $(message.html);
        //node.hide();
        var scroll = false;
        if($("#inbox").scrollTop()==$("#inbox")[0].scrollHeight-$("#inbox").outerHeight()) {
            scroll=true;
        }
        $("#inbox").append(node);
        //node.slideDown('fast');
        fixHeight(scroll);



    }
};
