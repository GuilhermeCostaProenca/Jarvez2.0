import { AbilityEffects } from '../../../Ability/AbilityEffects';
import { type SkillName } from '../../../Skill';
import { RaceAbility } from '../../RaceAbility';
import { DeformityEffect } from './DeformityEffect';
export declare class Deformity extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: DeformityEffect;
        };
    }>;
    constructor();
    addDeformity(choices: SkillName): void;
    serializeChoices(): {
        type: "skill";
        name: SkillName;
    }[];
}
