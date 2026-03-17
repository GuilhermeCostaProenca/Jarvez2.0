import { Action, type ActionSubClassParams } from './Action';
export declare class PickGrantedPower extends Action<'pickGrantedPower'> {
    constructor(params: ActionSubClassParams<'pickGrantedPower'>);
    execute(): void;
    getDescription(): string;
}
