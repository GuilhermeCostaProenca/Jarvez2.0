"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SonOfTormentaEffect = void 0;
const Ability_1 = require("../../../Ability");
const AddResistance_1 = require("../../../Action/AddResistance");
const ResistanceName_1 = require("../../../Resistance/ResistanceName");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class SonOfTormentaEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.sonOfTormenta);
        this.description = 'Você é uma criatura do tipo monstro '
            + 'e recebe +5 em testes de resistência contra efeitos causados por Lefeu e '
            + 'pela Tormenta.';
    }
    apply(transaction) {
        const addLefeuResistance = new AddResistance_1.AddResistance({
            payload: {
                resistance: ResistanceName_1.ResistanceName.lefeu,
                value: 5,
                source: this.source,
            },
            transaction,
        });
        const addTormentaResistance = new AddResistance_1.AddResistance({
            payload: {
                resistance: ResistanceName_1.ResistanceName.tormenta,
                value: 5,
                source: this.source,
            },
            transaction,
        });
        transaction.run(addLefeuResistance);
        transaction.run(addTormentaResistance);
    }
}
exports.SonOfTormentaEffect = SonOfTormentaEffect;
