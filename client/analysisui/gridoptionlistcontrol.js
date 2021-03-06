'use strict';

var $ = require('jquery');
var _ = require('underscore');
var GridControl = require('./gridcontrol');
var OptionListControl = require('./optionlistcontrol');

var GridOptionListControl = function(option, params) {
    GridControl.extend(this);
    OptionListControl.extendTo(this, option, params);

    this.onRenderToGrid = function(grid, row, column) {

        this.setAutoSizeHeight(false);
        var cell = grid.addLayout(column, row, false, this);
        cell.setStretchFactor(0.5);
        //cell.dockContentWidth = true;
        cell.dockContentHeight = true;

        return { height: 1, width: 1 };
    };
};

module.exports = GridOptionListControl;
