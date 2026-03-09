import type { AbilityName } from '../../Ability/Ability';
import { PassiveEffect } from '../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../Sheet/TransactionInterface';
import { SkillName } from '../../Skill/SkillName';
export declare class SpecialFriendEffect extends PassiveEffect {
    readonly skill: SkillName;
    static description: string;
    get description(): string;
    constructor(source: AbilityName, skill: SkillName);
    apply(transaction: TransactionInterface): void;
    private validateSkill;
}
