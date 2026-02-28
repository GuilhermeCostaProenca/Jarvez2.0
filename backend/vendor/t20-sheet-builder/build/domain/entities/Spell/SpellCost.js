"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpellCost = void 0;
const ManaCost_1 = require("../ManaCost");
const SpellCircleManaCost_1 = require("./SpellCircleManaCost");
class SpellCost extends ManaCost_1.ManaCost {
    constructor(circle) {
        super(SpellCircleManaCost_1.circleManaCost[circle]);
    }
}
exports.SpellCost = SpellCost;
