"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleAbility = void 0;
const Ability_1 = require("../Ability/Ability");
class RoleAbility extends Ability_1.Ability {
    constructor(name) {
        super(name, 'role');
        this.name = name;
    }
    serialize() {
        return {
            effects: this.effects.serialize(),
            name: this.name,
            abilityType: 'role',
        };
    }
}
exports.RoleAbility = RoleAbility;
