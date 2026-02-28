"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.JointerEffect = void 0;
const Ability_1 = require("../../Ability");
const ChangeClimbingDisplacement_1 = require("../../Action/ChangeClimbingDisplacement");
const ChangeVision_1 = require("../../Action/ChangeVision");
const Sheet_1 = require("../../Sheet");
const RaceAbilityName_1 = require("../RaceAbilityName");
class JointerEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.jointer);
        this.description = 'Você recebe visão no escuro'
            + ' e deslocamento de escalada igual ao seu deslocamento'
            + ' terrestre.';
    }
    apply(transaction) {
        transaction.run(new ChangeVision_1.ChangeVision({
            payload: {
                vision: Sheet_1.Vision.dark,
                source: this.source,
            },
            transaction,
        }));
        transaction.run(new ChangeClimbingDisplacement_1.ChangeClimbingDisplacement({
            payload: {
                climbingDisplacement: transaction.sheet.getSheetDisplacement().getDisplacement(),
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.JointerEffect = JointerEffect;
