/* jshint evil: true, strict: true */

'use strict';

var _ = require('underscore');
var $ = require('jquery');
var Backbone = require('backbone');
Backbone.$ = $;

var Options = require('./options');
var OptionsView = require('./optionsview');
var LayoutDef = require('./layoutdef');
var FormatDef = require('./formatdef');
var ControlManager = require('./controlmanager');
var SilkyControlManager = require('./silkycontrolmanager');
var LayoutActionManager = require('./layoutactionmanager');

window._ = _;

function addMsgListener(cmd, callback, failed) {
    window.addEventListener("message",
        function (e) {
            //try {

                var msg = e.data;
                if (msg.cmd !== cmd)
                    return;

                callback(msg.data);
            //} catch (e) {
            //    failed(e);
            //}
        }, false);
}

function sendMsg(id, data) {
    var msg = { cmd: id, data: data };
    window.parent.postMessage(msg, '*');
}

var Analysis = function(def, resources, baseControls) {

    eval(def);

    var options = module.exports.options;

    var controls = baseControls;
    if (_.isUndefined(module.exports.customControls) === false) {
        controls = module.exports.customControls;
        controls.setBaseControls(baseControls);
    }

    var layoutDef = new module.exports.LayoutDef();
    var actionManager = new LayoutActionManager(layoutDef);
    this.model = { options: new Options(options), layoutDef: layoutDef, resources: resources, controls: controls, actionManager: actionManager };

    this.View = new OptionsView( this.model);
};

var analysis = null;
var _def = null;
var _analysisResources = null;
var errored = false;
var $header = null;
var $hide = null;

var _controlManager = new SilkyControlManager();


$(document).ready(function() {

    $(document).mousedown(this, mouseDown);
    $(document).mouseup(this, mouseUp);
    $(document).mousemove(this, mouseMove);

    addMsgListener("options.def", loadAnalysisDef, loadFailed);
    addMsgListener("analysis.context", setResources);
    addMsgListener("options.changed", setOptionsValues);

    sendMsg("document.ready");

    $(window).resize( updateContainerHeight );
});

function loadAnalysisDef(def) {
    _def = def;
    if (_def !== null && _analysisResources !== null)
        loadAnalysis(_def, _analysisResources);
}

function loadAnalysis(def, resources) {
    analysis = new Analysis(def, resources, _controlManager);

    var title = analysis.model.layoutDef.getTitle();
    console.log("loading - " + title + "...");
    var $title = $('.silky-options-title');
    $title.empty();
    $title.append(title);

    $('body').append(analysis.View.$el);
    analysis.View.render();

    var $hide = $('.silky-sp-back-button');
    $hide.on("click", function(event) {
        closeOptions();
    });

    analysis.model.options.on('options.valuesForServer', onValuesForServerChanges);

    updateContainerHeight();
}

function loadFailed(e) {
    errored = true;
    console.log(e);
}

function setResources(resources) {

    _analysisResources = resources;

    if (analysis === null) {
        if (_analysisResources && _def !== null)
            loadAnalysis(_def, _analysisResources);
    }
    else
        analysis.model.resources = resources;
}

function setOptionsValues(data) {

    analysis.View.beginDataInitialisation();
    var model = analysis.model;
    var params = Options.getDefaultEventParams("changed");
    params.silent = true;
    model.options.beginEdit();
    _.each(data, function(value, key, list) {
        model.options.setOptionValue(key, value, params);
    });
    model.options.endEdit();
    analysis.View.endDataInitialisation();
}

function onValuesForServerChanges(e) {

    var compiledList = {};

    _.each(e.map, function(value, key, list) {
        compiledList[key] = value.option.getValue();
    });

    /*for (var i = 0; i < e.data.length; i++)
        list[e.data[i].name] = e.data[i].option.getValue();*/

    sendMsg("options.changed", compiledList);
}


function mouseUp(event) {
    var data = {
        eventName: "mouseup",
        which: event.which,
        pageX: event.pageX,
        pageY: event.pageY
    };

    sendMsg("document.mouse", data);
}

function mouseMove(event) {
    var data = {
        eventName: "mousemove",
        which: event.which,
        pageX: event.pageX,
        pageY: event.pageY
    };

    sendMsg("document.mouse", data);
}

function mouseDown(event) {
    var data = {
        eventName: "mousedown",
        which: event.which,
        pageX: event.pageX,
        pageY: event.pageY
    };

    sendMsg("document.mouse", data);
}


function closeOptions() {
    sendMsg("options.close");
}

function updateContainerHeight() {

    if (analysis === null)
        return;

    var $content = $('.silky-options-content');

    var pos = $content.position();

    var properties = $('body').css(["height", "padding-top", "padding-bottom", "border-top", "border-bottom"]);
    var height = parseFloat(properties.height) - parseFloat(properties["padding-top"]) - parseFloat(properties["padding-bottom"]) - parseFloat(properties["border-top"]) - parseFloat(properties["border-bottom"]);

    var value = height - pos.top;

    $content.css("height", value);
}
