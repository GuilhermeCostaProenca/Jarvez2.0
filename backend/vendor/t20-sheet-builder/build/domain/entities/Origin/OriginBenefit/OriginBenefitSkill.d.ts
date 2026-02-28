import { type TransactionInterface } from '../../Sheet/TransactionInterface';
import type { SkillName } from '../../Skill/SkillName';
import { type TranslatableName } from '../../Translator';
import { OriginBenefit } from './OriginBenefit';
import { type OriginBenefits } from './OriginBenefits';
import { type SerializedOriginBenefitSkill } from './SerializedOriginBenefit';
export declare class OriginBenefitSkill extends OriginBenefit {
    readonly skill: SkillName;
    name: SkillName;
    constructor(skill: SkillName);
    apply(transaction: TransactionInterface, source: TranslatableName): void;
    validate(originBenefits: OriginBenefits): void;
    serialize(): SerializedOriginBenefitSkill;
}
