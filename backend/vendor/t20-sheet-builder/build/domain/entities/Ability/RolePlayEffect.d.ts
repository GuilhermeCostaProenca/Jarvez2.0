import type { AbilityName } from './Ability';
import { AbilityEffect } from './AbilityEffect';
export declare class RolePlayEffect extends AbilityEffect {
    readonly description: string;
    constructor(source: AbilityName, description: string);
}
