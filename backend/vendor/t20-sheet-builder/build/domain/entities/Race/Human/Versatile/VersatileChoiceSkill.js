"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VersatileChoiceSkill = void 0;
const TrainSkill_1 = require("../../../Action/TrainSkill");
const VersatileChoice_1 = require("./VersatileChoice");
class VersatileChoiceSkill extends VersatileChoice_1.VersatileChoice {
    constructor(skill) {
        super(skill, 'skill');
        this.skill = skill;
    }
    addToSheet(transaction, source) {
        transaction.run(new TrainSkill_1.TrainSkill({
            payload: {
                skill: this.skill,
                source,
            },
            transaction,
        }));
    }
    serialize() {
        return {
            name: this.skill,
            type: 'skill',
        };
    }
}
exports.VersatileChoiceSkill = VersatileChoiceSkill;
