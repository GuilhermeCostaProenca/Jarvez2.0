import { type TriggeredEffect, type TriggerEvent } from '../Ability';
import { type TriggeredEffectMap } from '../Map';
export declare class SheetTriggeredEffects {
    readonly effects: Record<TriggerEvent, TriggeredEffectMap>;
    getByEvent(event: TriggerEvent): TriggeredEffectMap;
    registerEffect(events: TriggerEvent[], effect: TriggeredEffect): void;
}
