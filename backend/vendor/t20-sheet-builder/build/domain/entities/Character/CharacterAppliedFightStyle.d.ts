import { type FightStyle } from '../Power/GeneralPower/CombatPower/FightStyle/FightStyle';
import type { CharacterModifiers } from './CharacterModifiers';
export declare class CharacterAppliedFightStyle {
    readonly fightStyle: FightStyle;
    readonly indexesToRemove: {
        attack?: {
            contextual: number[];
        };
        defense?: {
            contextual: number[];
        };
    };
    constructor(fightStyle: FightStyle, indexesToRemove: {
        attack?: {
            contextual: number[];
        };
        defense?: {
            contextual: number[];
        };
    });
    removeModifiers(modifiers: CharacterModifiers): void;
}
