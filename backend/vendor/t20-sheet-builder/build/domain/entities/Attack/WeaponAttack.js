"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeaponAttack = void 0;
const Attack_1 = require("./Attack");
class WeaponAttack extends Attack_1.Attack {
    constructor(weapon) {
        super(weapon.damage, weapon.critical, weapon.name);
        this.weapon = weapon;
        this.selectedPurposeIndex = 0;
    }
    getTestDefaultSkill() {
        const purpose = this.weapon.purposes[this.selectedPurposeIndex];
        return purpose.defaultSkill;
    }
    selectPurpose(index) {
        this.selectedPurposeIndex = index;
    }
    getDamageAttribute() {
        const purpose = this.weapon.purposes[this.selectedPurposeIndex];
        return purpose.damageAttribute;
    }
    getCustomTestAttributes() {
        const purpose = this.weapon.purposes[this.selectedPurposeIndex];
        return purpose.customTestAttributes;
    }
}
exports.WeaponAttack = WeaponAttack;
