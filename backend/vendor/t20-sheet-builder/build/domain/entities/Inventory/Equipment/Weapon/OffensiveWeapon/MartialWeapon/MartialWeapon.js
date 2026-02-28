"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MartialWeapon = void 0;
const Proficiency_1 = require("../../../../../Sheet/Proficiency");
const OffensiveWeapon_1 = require("../OffensiveWeapon");
class MartialWeapon extends OffensiveWeapon_1.OffensiveWeapon {
    constructor() {
        super(Proficiency_1.Proficiency.martial);
    }
}
exports.MartialWeapon = MartialWeapon;
