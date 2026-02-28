import { ActivateableAbilityEffect } from '../../../Ability';
import { type Cost } from '../../../Sheet';
export declare class InspirationEffect extends ActivateableAbilityEffect {
    baseCosts: Cost[];
    description: string;
    constructor();
}
