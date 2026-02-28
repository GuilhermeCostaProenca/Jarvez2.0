import { AbilityEffects } from '../../../Ability/AbilityEffects';
import { RaceAbility } from '../../RaceAbility';
import { RockKnowledgeEffect } from './RockKnowledgeEffect';
export declare class RockKnowledge extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: RockKnowledgeEffect;
        };
    }>;
    constructor();
}
