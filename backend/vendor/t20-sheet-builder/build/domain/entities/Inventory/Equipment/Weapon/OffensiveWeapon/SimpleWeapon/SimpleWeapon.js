"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SimpleWeapon = void 0;
const Proficiency_1 = require("../../../../../Sheet/Proficiency");
const OffensiveWeapon_1 = require("../OffensiveWeapon");
class SimpleWeapon extends OffensiveWeapon_1.OffensiveWeapon {
    constructor() {
        super(Proficiency_1.Proficiency.simple);
    }
}
exports.SimpleWeapon = SimpleWeapon;
