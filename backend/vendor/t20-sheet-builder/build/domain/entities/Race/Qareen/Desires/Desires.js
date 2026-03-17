"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Desires = void 0;
const Ability_1 = require("../../../Ability");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class Desires extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.desires);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new Ability_1.RolePlayEffect(RaceAbilityName_1.RaceAbilityName.desires, Desires.effectDescription),
            },
        });
    }
}
exports.Desires = Desires;
Desires.effectDescription = 'Se lançar uma magia que alguém tenha'
    + ' pedido desde seu último turno, o custo da magia'
    + ' diminui em –1 PM. Fazer um desejo ao qareen é uma'
    + ' ação livre.';
