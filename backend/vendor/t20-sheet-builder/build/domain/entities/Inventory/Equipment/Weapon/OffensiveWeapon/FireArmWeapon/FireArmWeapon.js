"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FireArmWeapon = void 0;
const Proficiency_1 = require("../../../../../Sheet/Proficiency");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const OffensiveWeapon_1 = require("../OffensiveWeapon");
class FireArmWeapon extends OffensiveWeapon_1.OffensiveWeapon {
    constructor() {
        super(Proficiency_1.Proficiency.fire);
        this.purposes = FireArmWeapon.purposes;
    }
}
exports.FireArmWeapon = FireArmWeapon;
FireArmWeapon.purposes = [
    new WeaponPurpose_1.WeaponPurposeRangedShooting(),
];
