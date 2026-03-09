import { type BuildingSheet } from '../Sheet';
import { Action, type ActionSubClassParams } from './Action';
export declare class ChooseRace extends Action<'chooseRace', BuildingSheet> {
    constructor(params: ActionSubClassParams<'chooseRace', BuildingSheet>);
    execute(): void;
    getDescription(): string;
}
