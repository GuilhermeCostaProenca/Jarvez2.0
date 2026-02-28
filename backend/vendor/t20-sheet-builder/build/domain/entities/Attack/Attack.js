"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Attack = void 0;
const Skill_1 = require("../Skill");
class Attack {
    constructor(damage, critical, name) {
        this.damage = damage;
        this.critical = critical;
        this.name = name;
    }
    roll(random, skill) {
        const test = skill.roll(random, this.critical.threat);
        const damage = this.rollDamage(random);
        if (test.isCritical) {
            for (let i = 1; i < this.critical.multiplier; i++) {
                damage.append(this.rollDamage(random));
            }
        }
        return {
            test,
            damage,
        };
    }
    rollDamage(random) {
        return this.damage.roll(random);
    }
    getTestDefaultSkill() {
        return Skill_1.SkillName.fight;
    }
    getDamageAttribute() {
        return undefined;
    }
    getCustomTestAttributes() {
        return new Set(['strength']);
    }
    serialize() {
        return {
            damage: this.damage.serialize(),
            critical: this.critical.serialize(),
            name: this.name,
        };
    }
}
exports.Attack = Attack;
