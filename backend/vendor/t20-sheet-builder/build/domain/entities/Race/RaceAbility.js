"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RaceAbility = void 0;
const Ability_1 = require("../Ability/Ability");
class RaceAbility extends Ability_1.Ability {
    constructor(name) {
        super(name, 'race');
        this.name = name;
    }
    serialize() {
        return {
            abilityType: this.abilityType,
            effects: this.effects.serialize(),
            name: this.name,
        };
    }
}
exports.RaceAbility = RaceAbility;
