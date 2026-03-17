"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HalfResistanceDamageApplier = void 0;
class HalfResistanceDamageApplier {
    constructor(maxDamage, difficulty, damageType, resistSkill) {
        this.maxDamage = maxDamage;
        this.difficulty = difficulty;
        this.damageType = damageType;
        this.resistSkill = resistSkill;
    }
    apply(creature) {
        const resisted = creature.resist(this.difficulty, this.resistSkill);
        if (resisted) {
            creature.receiveDamage(Math.floor(this.maxDamage / 2), this.damageType);
            return;
        }
        creature.receiveDamage(this.maxDamage, this.damageType);
    }
}
exports.HalfResistanceDamageApplier = HalfResistanceDamageApplier;
