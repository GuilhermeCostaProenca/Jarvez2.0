"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Powers = void 0;
const GeneralPower_1 = require("./GeneralPower");
const GeneralPowers_1 = require("./GeneralPower/GeneralPowers");
const GrantedPowers_1 = require("./GrantedPower/GrantedPowers");
class Powers {
    getAll() {
        return Object.values(Powers.map);
    }
}
exports.Powers = Powers;
Powers.map = Object.assign(Object.assign(Object.assign({}, GeneralPowers_1.GeneralPowers.map), GrantedPowers_1.GrantedPowers.map), GeneralPower_1.TormentaPowers.map);
