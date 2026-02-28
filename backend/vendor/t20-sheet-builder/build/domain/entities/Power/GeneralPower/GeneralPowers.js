"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GeneralPowers = void 0;
const GrantedPowers_1 = require("../GrantedPower/GrantedPowers");
const CombatPower_1 = require("./CombatPower");
const DestinyPower_1 = require("./DestinyPower");
const Shell_1 = require("./TormentaPower/Shell/Shell");
class GeneralPowers {
    static getAll() {
        return Object.values(this.map);
    }
}
exports.GeneralPowers = GeneralPowers;
GeneralPowers.map = Object.assign({ dodge: CombatPower_1.Dodge, ironWill: DestinyPower_1.IronWill, medicine: DestinyPower_1.Medicine, oneWeaponStyle: CombatPower_1.OneWeaponStyle, shell: Shell_1.Shell }, GrantedPowers_1.GrantedPowers.map);
