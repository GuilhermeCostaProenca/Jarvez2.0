"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PlantsFriendEffect = void 0;
const Ability_1 = require("../../Ability");
const LearnSpell_1 = require("../../Action/LearnSpell");
const ControlPlants_1 = require("../../Spell/ControlPlants/ControlPlants");
const RaceAbilityName_1 = require("../RaceAbilityName");
class PlantsFriendEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.plantsFriend);
        this.description = 'Você pode lançar a magia'
            + ' Controlar Plantas (atributo-chave Sabedoria). Caso'
            + ' aprenda novamente essa magia, seu custo diminui'
            + ' em –1 PM.';
    }
    apply(transaction) {
        transaction.run(new LearnSpell_1.LearnSpell({
            payload: {
                source: RaceAbilityName_1.RaceAbilityName.plantsFriend,
                spell: new ControlPlants_1.ControlPlants(),
                needsCircle: false,
                needsSchool: false,
            },
            transaction,
        }));
    }
}
exports.PlantsFriendEffect = PlantsFriendEffect;
