"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginBenefitSkill = void 0;
const TrainSkill_1 = require("../../Action/TrainSkill");
const SheetBuilderError_1 = require("../../../errors/SheetBuilderError");
const OriginBenefit_1 = require("./OriginBenefit");
class OriginBenefitSkill extends OriginBenefit_1.OriginBenefit {
    constructor(skill) {
        super();
        this.skill = skill;
        this.name = skill;
    }
    apply(transaction, source) {
        transaction.run(new TrainSkill_1.TrainSkill({
            payload: {
                skill: this.skill,
                source,
            },
            transaction,
        }));
    }
    validate(originBenefits) {
        if (!originBenefits.skills.includes(this.skill)) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_ORIGIN_SKILL');
        }
    }
    serialize() {
        return {
            type: 'skills',
            name: this.skill,
        };
    }
}
exports.OriginBenefitSkill = OriginBenefitSkill;
