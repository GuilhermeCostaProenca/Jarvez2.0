"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExoticWeapon = void 0;
const Proficiency_1 = require("../../../../../Sheet/Proficiency");
const OffensiveWeapon_1 = require("../OffensiveWeapon");
class ExoticWeapon extends OffensiveWeapon_1.OffensiveWeapon {
    constructor() {
        super(Proficiency_1.Proficiency.exotic);
    }
}
exports.ExoticWeapon = ExoticWeapon;
