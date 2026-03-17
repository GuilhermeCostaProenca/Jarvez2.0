import { AbilityEffects } from '../../../Ability';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import { type SkillName } from '../../../Skill';
import { RoleAbility } from '../../RoleAbility';
import { SpecialistEffect } from './SpecialistEffect';
export declare class Specialist extends RoleAbility {
    effects: AbilityEffects<{
        triggered: {
            default: SpecialistEffect;
        };
    }>;
    constructor(skills: Set<SkillName>);
    addToSheet(transaction: TransactionInterface): void;
    getSkills(): SkillName[];
    private validateSkills;
}
