"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeaponPurposeRanged = void 0;
const Skill_1 = require("../../../../Skill");
const WeaponPurpose_1 = require("./WeaponPurpose");
class WeaponPurposeRanged extends WeaponPurpose_1.WeaponPurpose {
    constructor(params) {
        super(Object.assign({ defaultSkill: Skill_1.SkillName.aim }, params));
    }
}
exports.WeaponPurposeRanged = WeaponPurposeRanged;
