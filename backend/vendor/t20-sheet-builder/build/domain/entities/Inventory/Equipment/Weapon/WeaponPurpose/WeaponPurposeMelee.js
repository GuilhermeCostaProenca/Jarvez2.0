"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeaponPurposeMelee = void 0;
const Skill_1 = require("../../../../Skill");
const WeaponPurpose_1 = require("./WeaponPurpose");
class WeaponPurposeMelee extends WeaponPurpose_1.WeaponPurpose {
    constructor(params = {}) {
        var _a;
        super(Object.assign({ defaultSkill: Skill_1.SkillName.fight, damageAttribute: (_a = params.damageAttribute) !== null && _a !== void 0 ? _a : 'strength' }, params));
    }
}
exports.WeaponPurposeMelee = WeaponPurposeMelee;
