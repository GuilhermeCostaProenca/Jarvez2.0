"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FightStyle = void 0;
const GeneralPower_1 = require("../../GeneralPower");
const GeneralPowerGroup_1 = require("../../GeneralPowerGroup");
class FightStyle extends GeneralPower_1.GeneralPower {
    constructor() {
        super(...arguments);
        this.group = GeneralPowerGroup_1.GeneralPowerGroup.combat;
    }
}
exports.FightStyle = FightStyle;
